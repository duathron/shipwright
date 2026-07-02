"""Tests for the SSRF host-allowlist guard.

Coverage note: this primitive is the pre-committed guardrail for W3 (ollama
base_url made configurable) — it is deliberately unwired today, so there is
no call-site test here, only the primitive's own contract.
"""

from __future__ import annotations

import socket

import pytest

from shipwright_kit.security.ssrf import UnsafeURLError, assert_safe_url, is_safe_url


class TestSafeURLs:
    def test_loopback_allowed_with_allow_loopback(self):
        assert_safe_url("http://localhost:11434", allow_loopback=True)

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

    def test_resolve_false_skips_dns_and_allows_unresolvable_hostname(self, monkeypatch):
        def fake_getaddrinfo(*args, **kwargs):
            raise AssertionError("getaddrinfo must not be called when resolve=False")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        assert_safe_url("http://api.example.com", resolve=False)

    def test_resolve_true_raises_on_dns_failure(self, monkeypatch):
        def fake_getaddrinfo(host, port, *args, **kwargs):
            raise socket.gaierror("name resolution failed")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        with pytest.raises(UnsafeURLError):
            assert_safe_url("http://nonexistent.invalid", resolve=True)


class TestExports:
    def test_exports_available_from_security_package(self):
        from shipwright_kit.security import (  # noqa: F401
            UnsafeURLError,
            assert_safe_url,
            is_safe_url,
        )
