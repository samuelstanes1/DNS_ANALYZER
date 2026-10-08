"""Unit tests for DNSAnalyzerService."""

import pytest
from unittest.mock import MagicMock, patch
import dns.resolver
import dns.exception

from app.services.dns_service import DNSAnalyzerService, RECORD_TYPES


@pytest.fixture
def service():
    """Create a DNSAnalyzerService instance for testing."""
    return DNSAnalyzerService(timeout=2.0)


def test_sanitize_domain(service):
    """Test domain normalization and sanitization."""
    assert service.sanitize_domain("google.com") == "google.com"
    assert service.sanitize_domain("  GOOGLE.COM  ") == "google.com"
    assert service.sanitize_domain("https://example.com/path?query=1") == "example.com"
    assert service.sanitize_domain("http://sub.domain.org:8080/test") == "sub.domain.org"
    assert service.sanitize_domain("example.com.") == "example.com"
    assert service.sanitize_domain("") == ""
    assert service.sanitize_domain(None) == ""


def test_analyze_empty_or_invalid_domain(service):
    """Test analysis on empty or invalid input string."""
    result = service.analyze_domain("")
    assert result["is_resolvable"] is False
    assert result["status"] == "INVALID"
    assert "domain" in result["errors"]


def test_analyze_valid_domain(service):
    """Test analysis for a known valid live domain (google.com)."""
    result = service.analyze_domain("google.com")
    
    assert result["domain"] == "google.com"
    assert result["is_resolvable"] is True
    assert result["status"] in ("HEALTHY", "DEGRADED")
    assert isinstance(result["records"], dict)
    
    # Check that required record keys exist
    for rtype in RECORD_TYPES:
        assert rtype in result["records"]
        assert isinstance(result["records"][rtype], list)

    assert len(result["records"]["A"]) > 0
    assert len(result["records"]["NS"]) > 0
    assert result["response_time_ms"] > 0


def test_analyze_domain_missing_certain_record_types(service):
    """Test domain that has A records but no CNAME records."""
    result = service.analyze_domain("example.com")
    assert result["domain"] == "example.com"
    assert result["is_resolvable"] is True
    assert "A" in result["records"]
    assert len(result["records"]["A"]) > 0
    assert result["records"]["CNAME"] == []


def test_single_failed_record_does_not_fail_entire_analysis(service):
    """Ensure that a timeout on one record type (e.g. TXT) does NOT fail the entire analysis."""
    original_resolve = service.resolver.resolve

    def mock_resolve(domain, rtype):
        if rtype == "TXT":
            raise dns.resolver.Timeout()
        return original_resolve(domain, rtype)

    with patch.object(service.resolver, "resolve", side_effect=mock_resolve):
        result = service.analyze_domain("google.com")
        assert result["is_resolvable"] is True
        assert result["status"] in ("HEALTHY", "DEGRADED")
        assert len(result["records"]["A"]) > 0
        assert "TXT" in result["errors"]
        assert "timed out" in result["errors"]["TXT"].lower()


def test_analyze_non_resolvable_domain(service):
    """Test analysis for an invalid/non-existent domain safely."""
    fake_domain = "non-existent-domain-xyz-1234567890-test.invalid"
    result = service.analyze_domain(fake_domain)
    
    assert result["domain"] == fake_domain
    assert result["is_resolvable"] is False
    assert result["status"] == "UNRESOLVABLE"
    assert all(len(records) == 0 for records in result["records"].values())


def test_handle_timeout_exception(service):
    """Test safe handling when all DNS queries encounter a timeout."""
    with patch.object(service.resolver, "resolve", side_effect=dns.resolver.Timeout()):
        result = service.analyze_domain("timeout-domain.com")
        assert result["is_resolvable"] is False
        assert result["status"] == "UNRESOLVABLE"
        assert "A" in result["errors"]
        assert "timed out" in result["errors"]["A"].lower()


def test_handle_general_dns_exception(service):
    """Test safe handling when a generic DNSException occurs."""
    with patch.object(service.resolver, "resolve", side_effect=dns.exception.DNSException("Network failure")):
        result = service.analyze_domain("error-domain.com")
        assert result["is_resolvable"] is False
        assert result["status"] == "UNRESOLVABLE"
        assert "A" in result["errors"]
