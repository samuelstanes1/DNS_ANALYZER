"""Deterministic unit tests for DNSAnalyzerService with mocked DNS resolution."""

import pytest
from unittest.mock import MagicMock, patch
import dns.resolver
import dns.exception

from app.services.dns_service import DNSAnalyzerService, RECORD_TYPES


@pytest.fixture
def service():
    """Create an isolated DNSAnalyzerService instance."""
    return DNSAnalyzerService(timeout=1.0)


def create_mock_rdata(rtype: str, value: str):
    """Helper to create mock DNS rdata objects matching dnspython schema."""
    rdata = MagicMock()
    if rtype == "MX":
        rdata.preference = 10
        exchange_mock = MagicMock()
        exchange_mock.to_text.return_value = value
        rdata.exchange = exchange_mock
    elif rtype in ("NS", "CNAME"):
        target_mock = MagicMock()
        target_mock.to_text.return_value = value
        rdata.target = target_mock
    elif rtype == "TXT":
        rdata.strings = [value.encode("utf-8") if isinstance(value, str) else value]
    else:
        rdata.to_text.return_value = value
    return rdata


def test_sanitize_domain(service):
    """Test domain normalization and sanitization edge cases."""
    assert service.sanitize_domain("google.com") == "google.com"
    assert service.sanitize_domain("  GOOGLE.COM  ") == "google.com"
    assert service.sanitize_domain("https://example.com/path?query=1") == "example.com"
    assert service.sanitize_domain("http://sub.domain.org:8080/test") == "sub.domain.org"
    assert service.sanitize_domain("example.com.") == "example.com"
    assert service.sanitize_domain("") == ""
    assert service.sanitize_domain(None) == ""


def test_analyze_empty_or_invalid_domain(service):
    """Test analysis on empty domain string."""
    result = service.analyze_domain("")
    assert result["is_resolvable"] is False
    assert result["status"] == "INVALID"
    assert "domain" in result["errors"]
    assert result["response_time_ms"] == 0.0


def test_successful_dns_lookup_all_records(service):
    """Test successful resolution of all record types with deterministic mock."""
    mock_responses = {
        "A": [create_mock_rdata("A", "93.184.216.34")],
        "AAAA": [create_mock_rdata("AAAA", "2606:2800:220:1:248:1893:25c8:1946")],
        "MX": [create_mock_rdata("MX", "mail.example.com.")],
        "NS": [create_mock_rdata("NS", "ns1.example.com.")],
        "TXT": [create_mock_rdata("TXT", "v=spf1 ~all")],
        "CNAME": [create_mock_rdata("CNAME", "alias.example.com.")],
    }

    def mock_resolve(domain, rtype):
        if rtype in mock_responses:
            return mock_responses[rtype]
        raise dns.resolver.NoAnswer()

    with patch.object(service.resolver, "resolve", side_effect=mock_resolve):
        result = service.analyze_domain("example.com")

        assert result["domain"] == "example.com"
        assert result["is_resolvable"] is True
        assert result["status"] == "HEALTHY"
        assert result["records"]["A"] == ["93.184.216.34"]
        assert result["records"]["AAAA"] == ["2606:2800:220:1:248:1893:25c8:1946"]
        assert result["records"]["MX"] == ["10 mail.example.com"]
        assert result["records"]["NS"] == ["ns1.example.com"]
        assert result["records"]["TXT"] == ["v=spf1 ~all"]
        assert result["records"]["CNAME"] == ["alias.example.com"]
        assert result["errors"] == {}


def test_missing_record_types_handling(service):
    """Test DNS lookup when specific records (e.g. CNAME and AAAA) return NoAnswer."""
    def mock_resolve(domain, rtype):
        if rtype == "A":
            return [create_mock_rdata("A", "1.2.3.4")]
        if rtype == "NS":
            return [create_mock_rdata("NS", "ns1.example.com.")]
        # CNAME, AAAA, MX, TXT have no answer
        raise dns.resolver.NoAnswer()

    with patch.object(service.resolver, "resolve", side_effect=mock_resolve):
        result = service.analyze_domain("example.com")

        assert result["is_resolvable"] is True
        assert result["status"] == "HEALTHY"
        assert result["records"]["A"] == ["1.2.3.4"]
        assert result["records"]["NS"] == ["ns1.example.com"]
        assert result["records"]["CNAME"] == []
        assert result["records"]["AAAA"] == []
        assert result["records"]["MX"] == []
        assert result["records"]["TXT"] == []
        assert result["errors"] == {}


def test_failed_dns_lookup_nxdomain(service):
    """Test failed lookup when domain does not exist (NXDOMAIN)."""
    with patch.object(service.resolver, "resolve", side_effect=dns.resolver.NXDOMAIN()):
        result = service.analyze_domain("nonexistent-domain.com")

        assert result["is_resolvable"] is False
        assert result["status"] == "UNRESOLVABLE"
        assert all(records == [] for records in result["records"].values())
        assert "NXDOMAIN" in result["errors"]["A"]


def test_single_failed_record_does_not_fail_entire_analysis(service):
    """Ensure that a timeout on one record type (e.g. TXT) does not fail the entire analysis."""
    def mock_resolve(domain, rtype):
        if rtype == "A":
            return [create_mock_rdata("A", "142.250.190.46")]
        if rtype == "NS":
            return [create_mock_rdata("NS", "ns1.google.com.")]
        if rtype == "TXT":
            raise dns.resolver.Timeout()
        raise dns.resolver.NoAnswer()

    with patch.object(service.resolver, "resolve", side_effect=mock_resolve):
        result = service.analyze_domain("google.com")
        assert result["is_resolvable"] is True
        assert result["status"] == "HEALTHY"
        assert result["records"]["A"] == ["142.250.190.46"]
        assert "TXT" in result["errors"]
        assert "timed out" in result["errors"]["TXT"].lower()


def test_failed_dns_lookup_timeout(service):
    """Test safe handling when all DNS queries encounter a timeout."""
    with patch.object(service.resolver, "resolve", side_effect=dns.resolver.Timeout()):
        result = service.analyze_domain("timeout-domain.com")
        assert result["is_resolvable"] is False
        assert result["status"] == "UNRESOLVABLE"
        assert "A" in result["errors"]
        assert "timed out" in result["errors"]["A"].lower()


def test_failed_dns_lookup_no_nameservers(service):
    """Test safe handling when no nameservers reply."""
    with patch.object(service.resolver, "resolve", side_effect=dns.resolver.NoNameservers()):
        result = service.analyze_domain("no-ns-domain.com")
        assert result["is_resolvable"] is False
        assert result["status"] == "UNRESOLVABLE"
        assert "No nameservers" in result["errors"]["A"]


def test_failed_dns_lookup_generic_exception(service):
    """Test safe handling when generic DNSException occurs."""
    with patch.object(service.resolver, "resolve", side_effect=dns.exception.DNSException("Network failure")):
        result = service.analyze_domain("error-domain.com")
        assert result["is_resolvable"] is False
        assert result["status"] == "UNRESOLVABLE"
        assert "DNS resolution error" in result["errors"]["A"]
