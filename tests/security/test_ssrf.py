"""Tests for the SSRF host-allowlist guard.

Coverage note: this is a primitive callers wire explicitly, so there is no
call-site test here, only the primitive's own contract. No test may do real
DNS: the autouse ``mock_dns`` fixture replaces ``socket.getaddrinfo``.
"""

from __future__ import annotations

import socket

import pytest

from shipwright_kit.security.ssrf import UnsafeURLError, assert_safe_url, is_safe_url

_HOSTS: dict[str, str] = {
    "localhost": "127.0.0.1",
    "metadata.google.internal": "169.254.169.254",
    "example.com": "93.184.215.14",
    "api.example.com": "93.184.215.14",
}


def _info(addr: str):
    family = socket.AF_INET6 if ":" in addr else socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, "", (addr, 0))]


@pytest.fixture(autouse=True)
def mock_dns(monkeypatch):
    """Deterministic DNS: known names map to fixed addresses, others fail."""

    def fake_getaddrinfo(host, port, *args, **kwargs):
        if host in _HOSTS:
            return _info(_HOSTS[host])
        # Numeric literals are normalised by the real resolver; mimic inet_aton forms.
        try:
            return _info(socket.inet_ntoa(socket.inet_aton(host)))
        except OSError:
            raise socket.gaierror(f"no such host: {host}") from None

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


class TestSafeURLs:
    def test_loopback_allowed_with_allow_loopback(self):
        assert_safe_url("http://localhost:11434", allow_loopback=True)

    def test_public_https_example_allowed(self):
        assert_safe_url("https://example.com/")

    def test_loopback_ip_literal_allowed_with_allow_loopback(self):
        assert_safe_url("http://127.0.0.1:11434", allow_loopback=True)

    def test_public_https_host(self):
        assert_safe_url("https://api.example.com")

    def test_is_safe_url_true_for_safe(self):
        assert is_safe_url("https://api.example.com") is True


class TestUnsafeURLs:
    def test_cloud_metadata_ip_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://169.254.169.254/latest/meta-data")

    def test_rfc1918_10_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://10.0.0.1")

    def test_rfc1918_192_168_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://192.168.1.1")

    def test_rfc1918_172_16_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://172.16.0.5")

    def test_file_scheme_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("file:///etc/passwd")

    def test_ipv6_loopback_blocked_without_allow_loopback(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[::1]/")

    def test_ipv4_loopback_blocked_without_allow_loopback(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://127.0.0.1/")

    def test_ipv6_link_local_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[fe80::1]/")

    def test_ipv6_unique_local_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[fc00::1]/")

    def test_unsupported_scheme_ftp_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("ftp://example.com/file")

    def test_no_host_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("file:///no/host/here")

    def test_is_safe_url_false_for_unsafe(self):
        assert is_safe_url("http://10.0.0.1") is False

    def test_unsafe_url_error_is_value_error(self):
        assert issubclass(UnsafeURLError, ValueError)

    def test_multicast_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://224.0.0.1")

    def test_reserved_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://240.0.0.1")

    def test_empty_host_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://")

    def test_malformed_ipv6_bracket_raises_unsafe_url_error(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[::1")


class TestResolve:
    def test_resolve_true_rejects_hostname_resolving_to_private_ip(self, monkeypatch):
        def fake_getaddrinfo(host, port, *args, **kwargs):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 0)),
            ]

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://internal.example.com", resolve=True)

    def test_resolve_true_allows_hostname_resolving_to_public_ip(self, monkeypatch):
        def fake_getaddrinfo(host, port, *args, **kwargs):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            ]

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        assert_safe_url("http://public.example.com", resolve=True)

    def test_resolve_true_rejects_if_any_resolved_address_is_blocked(self, monkeypatch):
        def fake_getaddrinfo(host, port, *args, **kwargs):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0)),
            ]

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://mixed.example.com", resolve=True)

    def test_resolve_false_with_hostname_raises(self, monkeypatch):
        def fake_getaddrinfo(*args, **kwargs):
            raise AssertionError("getaddrinfo must not be called when resolve=False")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://api.example.com", resolve=False)

    def test_resolve_false_hostname_in_allow_hosts_passes_without_dns(self, monkeypatch):
        def fake_getaddrinfo(*args, **kwargs):
            raise AssertionError("getaddrinfo must not be called for an allow_hosts host")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        assert_safe_url("http://api.example.com", resolve=False, allow_hosts=frozenset({"api.example.com"}))

    def test_resolve_true_raises_on_dns_failure(self, monkeypatch):
        def fake_getaddrinfo(host, port, *args, **kwargs):
            raise socket.gaierror("name resolution failed")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://nonexistent.invalid", resolve=True)


class TestAllowHosts:
    def test_host_in_set_passes(self):
        assert_safe_url("http://internal.corp.example/", allow_hosts=frozenset({"internal.corp.example"}))

    def test_host_match_is_case_insensitive(self):
        assert_safe_url("http://Internal.Corp.Example/", allow_hosts=frozenset({"internal.corp.example"}))

    def test_host_not_in_set_with_resolve_false_raises(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://other.example/", resolve=False, allow_hosts=frozenset({"api.example.com"}))

    def test_ip_literal_still_checked_when_resolve_false(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://10.0.0.1/", resolve=False)


class TestBypassForms:
    """Audit F6 measured bypasses; each passed on the pre-fix code."""

    def test_localhost_resolving_to_loopback_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://localhost/")

    def test_metadata_google_internal_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://metadata.google.internal/")

    def test_decimal_integer_loopback_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://2130706433/")

    def test_short_form_loopback_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://127.1/")

    def test_hex_octet_loopback_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://0x7f.0.0.1/")

    def test_trailing_dot_metadata_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://169.254.169.254./")

    def test_alibaba_metadata_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://100.100.100.200/")

    def test_cgnat_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://100.64.0.1/")

    def test_ipv4_mapped_ipv6_metadata_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[::ffff:100.100.100.200]/")

    def test_ipv4_mapped_ipv6_loopback_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[::ffff:127.0.0.1]/")

    def test_ietf_protocol_assignments_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://192.0.0.9/")

    def test_nat64_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[64:ff9b::7f00:1]/")

    def test_ipv6_multicast_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[ff0e::1]/")

    def test_localhost_allowed_with_allow_loopback(self):
        assert_safe_url("http://localhost:11434/", allow_loopback=True)

    def test_loopback_literal_allowed_with_allow_loopback(self):
        assert_safe_url("http://127.0.0.1:11434/", allow_loopback=True)


class TestParserDifferential:
    """A1 item 1: urllib3/requests treat a backslash as a delimiter; urlsplit does not."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1:8080\\@example.com/",
            "http://169.254.169.254\\@evil.com/",
            "http://evil.com\\@169.254.169.254/",
            "http://example.com/\tpath",
            "http://example.com/ path",
            "http://example.com/\npath",
            "http://example.com/\x7fpath",
            "http://example.com/\x00path",
            "http://ex\u00e4mple.com/",
            "http://\u0435xample.com/",
        ],
        ids=lambda u: repr(u),
    )
    def test_rejected(self, url):
        with pytest.raises(UnsafeURLError):
            assert_safe_url(url)

    def test_backslash_guard_assert(self):
        assert "\\" in "http://127.0.0.1\\@example.com/"

    def test_plain_https_still_passes(self):
        assert_safe_url("https://example.com/")

    def test_urllib3_and_urlsplit_hosts_agree_for_accepted_urls(self):
        urllib3 = pytest.importorskip("urllib3")
        from urllib.parse import urlsplit

        poc = [
            "http://127.0.0.1:8080\\@example.com/",
            "http://169.254.169.254\\@evil.com/",
            "http://evil.com\\@169.254.169.254/",
            "http://169.254.169.254\\.evil.com/",
            "http://evil.com:80\\@169.254.169.254/",
            "http://example.com/",
        ]
        for url in poc:
            try:
                other = urllib3.util.parse_url(url).host
            except Exception:
                other = None
            if (urlsplit(url).hostname or "").lower() != (other or "").lower():
                with pytest.raises(UnsafeURLError):
                    assert_safe_url(url)

    def test_site_local_blocked(self):
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://[fec0::1]/")


class TestExports:
    def test_exports_available_from_security_package(self):
        from shipwright_kit.security import (  # noqa: F401
            UnsafeURLError,
            assert_safe_url,
            is_safe_url,
        )
