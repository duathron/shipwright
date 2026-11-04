"""SSRF host-allowlist guard for outbound HTTP requests.

A primitive that callers wire explicitly at their own outbound-request sites;
it is not applied automatically to any shipwright_kit transport (loopback and
private Ollama hosts are legitimate for ``shipwright_kit.llm``). Hostnames are
resolved by default (``resolve=True``) and every resolved address is checked.

Import-light: stdlib only (``ipaddress``, ``urllib.parse``, ``socket``) — no
third-party deps, no import-time side effects. Mirrors the import-light
invariant of ``shipwright_kit.security.injection``.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlsplit

__all__ = [
    "UnsafeURLError",
    "assert_safe_url",
    "is_safe_url",
]

_ALLOWED_SCHEMES = {"http", "https"}

_IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class UnsafeURLError(ValueError):
    """Raised by :func:`assert_safe_url` when a URL is unsafe to fetch."""


_EXTRA_BLOCKED_NETS = (
    ipaddress.ip_network("192.0.0.0/24"),  # IETF protocol assignments
    ipaddress.ip_network("64:ff9b::/96"),  # NAT64 (embeds an IPv4 address)
    ipaddress.ip_network("fec0::/10"),  # deprecated site-local
)


def _is_blocked_ip(ip: _IPAddress, *, allow_loopback: bool) -> bool:
    """True if `ip` should be blocked as an SSRF target.

    An IPv4-mapped IPv6 address (``::ffff:a.b.c.d``) is judged as its embedded
    IPv4 address. Loopback (127.0.0.0/8, ::1) is carved out first so
    ``allow_loopback`` can permit it; every other address that is not globally
    routable stays blocked unconditionally: link-local (incl. the
    169.254.169.254 cloud-metadata address), private/unique-local, CGNAT
    (100.64.0.0/10, incl. 100.100.100.200), multicast, reserved, unspecified,
    192.0.0.0/24 and the NAT64 prefix.
    """
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if ip.is_loopback:
        return not allow_loopback
    if ip.is_multicast or ip.is_unspecified or ip.is_reserved or ip.is_link_local or ip.is_private:
        return True
    if not ip.is_global:
        return True
    return any(ip.version == net.version and ip in net for net in _EXTRA_BLOCKED_NETS)


def _literal_ip(host: str) -> _IPAddress | None:
    """Parse `host` as an IP literal, incl. legacy IPv4 forms (``127.1``, ``2130706433``, ``0x7f.0.0.1``)."""
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    try:
        return ipaddress.IPv4Address(socket.inet_ntoa(socket.inet_aton(host)))
    except (OSError, ValueError):
        return None


def assert_safe_url(
    url: str,
    *,
    allow_loopback: bool = False,
    resolve: bool = True,
    allow_hosts: frozenset[str] | None = None,
) -> None:
    """Raise :class:`UnsafeURLError` if `url` is unsafe to fetch outbound; else return None.

    Blocks:
      - non-http(s) schemes (``file://``, ``ftp://``, etc.) and malformed URLs.
      - IP-literal hosts in RFC1918 private ranges (10/8, 172.16/12, 192.168/16),
        link-local ranges including the 169.254.169.254 cloud-metadata address
        (169.254.0.0/16), IPv6 unique-local (fc00::/7), IPv6 link-local
        (fe80::/10), and loopback (127.0.0.0/8, ::1) — unless
        ``allow_loopback=True``.

    ``resolve=True`` (the default): a non-IP-literal hostname is resolved via
    ``socket.getaddrinfo`` and rejected if ANY resolved address is blocked.
    With ``resolve=False`` a hostname cannot be vetted, so it raises unless it
    is in ``allow_hosts`` (a case-insensitive set of explicitly trusted
    hostnames, checked before DNS; a listed host skips resolution). IP-literal
    hosts, including legacy forms such as ``127.1`` or ``2130706433`` and a
    trailing dot, are always range-checked.

    URLs containing a backslash, a control character, a space or any non-ASCII
    character are rejected outright (parser-differential guard); callers must
    IDNA-encode internationalized hostnames to ASCII first.

    Caveat: this is a best-effort, TOCTOU-prone check. DNS is not pinned —
    the hostname can re-resolve to a different (unsafe) address between this
    check and the actual outbound request (a classic DNS-rebinding SSRF
    bypass). Callers with a hard safety requirement should connect to the
    resolved IP directly (not re-resolve the hostname) or maintain an
    explicit host allowlist; this function is a guardrail, not a substitute
    for that.
    """
    # Parser differential (CWE-918/436): urlsplit treats a backslash as an
    # ordinary character, while urllib3/requests treat it as a delimiter, so
    # ``http://127.0.0.1\\@example.com/`` would be vetted as example.com yet
    # fetched from loopback. Reject anything the two parsers could disagree on.
    if any(c == "\\" or c <= " " or c == "\x7f" or ord(c) > 0x7F for c in url):
        raise UnsafeURLError(f"URL contains a backslash, control, space or non-ASCII character: {url!r}")

    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise UnsafeURLError(f"malformed URL: {url!r}") from exc

    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeURLError(f"unsupported scheme: {scheme or '(none)'!r}")

    # Not wrapped in try/except: urlsplit() above already rejects malformed
    # IPv6-bracket netlocs before .hostname would ever raise.
    host = parsed.hostname
    if not host:
        raise UnsafeURLError(f"URL has no host: {url!r}")

    if host.endswith("."):
        host = host[:-1]
    literal_ip = _literal_ip(host)

    if literal_ip is not None:
        if _is_blocked_ip(literal_ip, allow_loopback=allow_loopback):
            raise UnsafeURLError(f"blocked address: {host}")
        return None

    if allow_hosts is not None and host.lower() in {h.lower() for h in allow_hosts}:
        return None

    if not resolve:
        raise UnsafeURLError(f"host {host!r} is not an IP literal and is not in allow_hosts (resolve=False)")

    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise UnsafeURLError(f"could not resolve host: {host!r} ({exc})") from exc
    for info in infos:
        sockaddr = info[4]
        resolved_ip = ipaddress.ip_address(sockaddr[0])
        if _is_blocked_ip(resolved_ip, allow_loopback=allow_loopback):
            raise UnsafeURLError(f"host {host!r} resolves to blocked address: {sockaddr[0]}")

    return None


def is_safe_url(url: str, **kwargs: Any) -> bool:
    """Convenience wrapper: True if `url` passes :func:`assert_safe_url`, else False."""
    try:
        assert_safe_url(url, **kwargs)
    except UnsafeURLError:
        return False
    return True
