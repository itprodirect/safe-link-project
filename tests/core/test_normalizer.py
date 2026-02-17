"""Unit tests for the URL canonicalization pipeline."""

from __future__ import annotations

from lsh.core.normalizer import (
    is_private_or_loopback,
    iterative_percent_decode,
    normalize_path,
    normalize_url,
    parse_host_to_ipv4,
    resolve_ipv6_mapped_v4,
)


class TestParseHostToIPv4:
    """Test integer/octal/hex/abbreviated IP parsing."""

    def test_integer_ip(self) -> None:
        ip, notes = parse_host_to_ipv4("2130706433")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("integer_ip" in n for n in notes)

    def test_hex_integer_ip(self) -> None:
        ip, notes = parse_host_to_ipv4("0x7f000001")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("hex_integer_ip" in n for n in notes)

    def test_octal_dotted_quad(self) -> None:
        ip, notes = parse_host_to_ipv4("0177.0000.0000.0001")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("octal_ip" in n for n in notes)

    def test_hex_dotted_quad(self) -> None:
        ip, notes = parse_host_to_ipv4("0x7f.0x0.0x0.0x1")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("hex_ip" in n for n in notes)

    def test_mixed_notation(self) -> None:
        ip, notes = parse_host_to_ipv4("0x7f.0.0.01")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("mixed_notation" in n for n in notes)

    def test_abbreviated_ip_two_parts(self) -> None:
        ip, notes = parse_host_to_ipv4("127.1")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("abbreviated_ip" in n for n in notes)

    def test_abbreviated_ip_three_parts(self) -> None:
        ip, notes = parse_host_to_ipv4("10.1.1")
        assert ip is not None
        assert str(ip) == "10.1.0.1"  # BSD: (10<<24)|(1<<16)|1
        assert any("abbreviated_ip" in n for n in notes)

    def test_standard_dotted_decimal(self) -> None:
        ip, notes = parse_host_to_ipv4("127.0.0.1")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert notes == []  # No normalization needed

    def test_public_ip(self) -> None:
        ip, _ = parse_host_to_ipv4("8.8.8.8")
        assert ip is not None
        assert str(ip) == "8.8.8.8"

    def test_not_an_ip_hostname(self) -> None:
        ip, notes = parse_host_to_ipv4("google.com")
        assert ip is None
        assert notes == []

    def test_empty_string(self) -> None:
        ip, notes = parse_host_to_ipv4("")
        assert ip is None
        assert notes == []

    def test_garbage_input(self) -> None:
        ip, notes = parse_host_to_ipv4("not-an-ip-at-all")
        assert ip is None
        assert notes == []

    def test_too_many_octets(self) -> None:
        ip, _notes = parse_host_to_ipv4("1.2.3.4.5")
        assert ip is None

    def test_octet_overflow(self) -> None:
        ip, _notes = parse_host_to_ipv4("0400.0.0.1")
        assert ip is None  # 0400 octal = 256, too large for 4-part

    def test_integer_overflow(self) -> None:
        ip, _notes = parse_host_to_ipv4("4294967296")
        assert ip is None  # > 0xFFFFFFFF

    def test_trailing_dot(self) -> None:
        ip, _notes = parse_host_to_ipv4("127.0.0.1.")
        assert ip is not None
        assert str(ip) == "127.0.0.1"


class TestResolveIPv6MappedV4:
    """Test IPv6-mapped IPv4 detection."""

    def test_mapped_loopback(self) -> None:
        ip, notes = resolve_ipv6_mapped_v4("::ffff:127.0.0.1")
        assert ip is not None
        assert str(ip) == "127.0.0.1"
        assert any("ipv6_mapped_v4" in n for n in notes)

    def test_mapped_public(self) -> None:
        ip, _notes = resolve_ipv6_mapped_v4("::ffff:8.8.8.8")
        assert ip is not None
        assert str(ip) == "8.8.8.8"

    def test_plain_ipv6(self) -> None:
        ip, _notes = resolve_ipv6_mapped_v4("::1")
        assert ip is None

    def test_not_ipv6(self) -> None:
        ip, _notes = resolve_ipv6_mapped_v4("google.com")
        assert ip is None

    def test_empty(self) -> None:
        ip, _notes = resolve_ipv6_mapped_v4("")
        assert ip is None


class TestIsPrivateOrLoopback:
    """Test private/loopback IP classification."""

    def test_loopback(self) -> None:
        from ipaddress import IPv4Address

        assert is_private_or_loopback(IPv4Address("127.0.0.1")) is True

    def test_private_10(self) -> None:
        from ipaddress import IPv4Address

        assert is_private_or_loopback(IPv4Address("10.0.0.1")) is True

    def test_public(self) -> None:
        from ipaddress import IPv4Address

        assert is_private_or_loopback(IPv4Address("8.8.8.8")) is False


class TestIterativePercentDecode:
    """Test percent-decode iteration."""

    def test_single_round(self) -> None:
        result, rounds = iterative_percent_decode("hello%20world")
        assert result == "hello world"
        assert rounds == 1

    def test_double_encoded(self) -> None:
        result, rounds = iterative_percent_decode("%2520")
        assert result == " "
        assert rounds == 2

    def test_no_encoding(self) -> None:
        result, rounds = iterative_percent_decode("hello")
        assert result == "hello"
        assert rounds == 0

    def test_cap_at_max_rounds(self) -> None:
        # Create a deeply nested encoding that would take many rounds
        value = "%25"
        for _ in range(10):
            value = value.replace("%", "%25")
        _, rounds = iterative_percent_decode(value)
        assert rounds <= 5  # Capped at max


class TestNormalizePath:
    """Test path normalization."""

    def test_empty(self) -> None:
        assert normalize_path("") == "/"

    def test_double_slash(self) -> None:
        assert normalize_path("//foo//bar") == "/foo/bar"

    def test_dot_segments(self) -> None:
        assert normalize_path("/foo/./bar") == "/foo/bar"

    def test_dotdot_segments(self) -> None:
        assert normalize_path("/foo/bar/../baz") == "/foo/baz"

    def test_combined(self) -> None:
        assert normalize_path("/foo/./bar/../baz//qux") == "/foo/baz/qux"


class TestNormalizeURL:
    """Test the full normalization pipeline."""

    def test_integer_ip_url(self) -> None:
        result = normalize_url("http://2130706433")
        assert "127.0.0.1" in result.canonical
        assert result.canonical_host == "127.0.0.1"
        assert any("integer_ip" in n for n in result.normalization_notes)

    def test_localhost_url(self) -> None:
        result = normalize_url("http://localhost")
        assert result.canonical_host == "127.0.0.1"
        assert any("localhost_alias" in n for n in result.normalization_notes)

    def test_encoded_hostname(self) -> None:
        result = normalize_url("http://%65%76%69%6c.com")
        assert result.canonical_host == "evil.com"
        assert any("percent_decoded" in n for n in result.normalization_notes)

    def test_ipv6_mapped_url(self) -> None:
        result = normalize_url("http://[::ffff:127.0.0.1]")
        assert result.canonical_host == "127.0.0.1"
        assert any("ipv6_mapped_v4" in n for n in result.normalization_notes)

    def test_default_port_removal(self) -> None:
        result = normalize_url("http://example.com:80/path")
        assert ":80" not in result.canonical
        assert any("default_port_removed" in n for n in result.normalization_notes)

    def test_non_default_port_preserved(self) -> None:
        result = normalize_url("http://example.com:8080/path")
        assert ":8080" in result.canonical

    def test_passthrough_normal_url(self) -> None:
        result = normalize_url("https://google.com/search?q=test")
        assert result.canonical_host == "google.com"
        assert "google.com" in result.canonical

    def test_empty_input(self) -> None:
        result = normalize_url("")
        assert result.canonical == ""
        assert result.normalization_notes == []

    def test_whitespace_only(self) -> None:
        result = normalize_url("   ")
        assert result.normalization_notes == []

    def test_octal_ip_url(self) -> None:
        result = normalize_url("http://0177.0000.0000.0001")
        assert result.canonical_host == "127.0.0.1"

    def test_hex_ip_url(self) -> None:
        result = normalize_url("http://0x7f.0x0.0x0.0x1")
        assert result.canonical_host == "127.0.0.1"

    def test_trailing_dot_removed(self) -> None:
        result = normalize_url("http://evil.com./path")
        assert result.canonical_host == "evil.com"

    def test_preserves_fragment(self) -> None:
        result = normalize_url("http://evil.com#@google.com")
        assert "#@google.com" in result.canonical

    def test_preserves_userinfo(self) -> None:
        result = normalize_url("http://user@evil.com")
        assert "user@" in result.canonical
