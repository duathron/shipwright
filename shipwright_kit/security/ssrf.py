"""SSRF host-allowlist guard for outbound HTTP requests.

Pre-committed guardrail for W3 (the LLM-provider layer making ollama's
``base_url`` configurable). This module is the primitive ONLY — it is not
wired into any tool or into ``ollama.py`` yet (``base_url`` is hardcoded
today, so wiring now would be dead code in the shipped path). W3 does the
wiring.

Import-light: stdlib only (``ipaddress``, ``urllib.parse``, ``socket``) — no
third-party deps, no import-time side effects. Mirrors the import-light
invariant of ``shipwright_kit.security.injection``.
"""

from __future__ import annotations

import ipaddress
import socket
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


def _is_blocked_ip(ip: _IPAddress, *, allow_loopback: bool) -> bool:
    """True if `ip` should be blocked as an SSRF target.

    Loopback (127.0.0.0/8, ::1) is carved out first so ``allow_loopback``
    can permit it — every other non-globally-routable range stays blocked
    unconditionally: link-local (169.254.0.0/16, incl. the 169.254.169.254
    cloud-metadata address, and IPv6 fe80::/10), RFC1918 private ranges and
    IPv6 unique-local (fc00::/7) via ``is_private``, plus multicast/
    reserved/unspecified as defense in depth.
    """
    if ip.is_loopback:
        return not allow_loopback
    if ip.is_link_local:
        return True
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True
    if ip.is_private:
        return True
    return False


def assert_safe_url(url: str, *, allow_loopback: bool = False, resolve: bool = False) -> None:
    """Raise :class:`UnsafeURLError` if `url` is unsafe to fetch outbound; else return None.

    Blocks:
      - non-http(s) schemes (``file://``, ``ftp://``, etc.) and malformed URLs.
      - IP-literal hosts in RFC1918 private ranges (10/8, 172.16/12, 192.168/16),
        link-local ranges including the 169.254.169.254 cloud-metadata address
        (169.254.0.0/16), IPv6 unique-local (fc00::/7), IPv6 link-local
        (fe80::/10), and loopback (127.0.0.0/8, ::1) — unless
        ``allow_loopback=True``.

    When ``resolve=True``, a non-IP-literal hostname is resolved via
    ``socket.getaddrinfo`` and rejected if ANY resolved address is blocked.

    Caveat: this is a best-effort, TOCTOU-prone check. DNS is not pinned —
    the hostname can re-resolve to a different (unsafe) address between this
    check and the actual outbound request (a classic DNS-rebinding SSRF
    bypass). Callers with a hard safety requirement should connect to the
    resolved IP directly (not re-resolve the hostname) or maintain an
    explicit host allowlist; this function is a guardrail, not a substitute
    for that.
    """
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

    try:
        literal_ip: _IPAddress | None = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        if _is_blocked_ip(literal_ip, allow_loopback=allow_loopback):
            raise UnsafeURLError(f"blocked address: {host}")
        return None

    if resolve:
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


def is_safe_url(url: str, **kwargs: bool) -> bool:
    """Convenience wrapper: True if `url` passes :func:`assert_safe_url`, else False."""
    try:
        assert_safe_url(url, **kwargs)
    except UnsafeURLError:
        return False
    return True
