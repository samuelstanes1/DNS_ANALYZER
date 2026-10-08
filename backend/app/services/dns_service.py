"""DNS Analysis Service.

Library Choice:
`dnspython` (https://www.dnspython.org/) was selected because:
1. It is the industry-standard, battle-tested Python DNS toolkit actively maintained since 2001.
2. It provides comprehensive support for all DNS record types (A, AAAA, MX, NS, TXT, CNAME, etc.).
3. It features granular exception handling (NXDOMAIN, NoAnswer, Timeout, NoNameservers) allowing
   safe, non-crashing diagnostics.
4. It is pure Python, lightweight, and standard across backend production architectures.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional
import dns.exception
import dns.resolver

logger = logging.getLogger("dns_analyzer.service")

# Standard DNS record types analyzed for domain health diagnostics
RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]


class DNSAnalyzerService:
    """Service responsible for performing isolated, safe DNS queries and health evaluations."""

    def __init__(self, nameservers: Optional[List[str]] = None, timeout: float = 3.0):
        """Initialize resolver with configurable timeout and optional custom nameservers."""
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout

        if nameservers:
            self.resolver.nameservers = nameservers
        else:
            # Fallback public nameservers (Google & Cloudflare) for consistent resolution
            self.resolver.nameservers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]

    @staticmethod
    def sanitize_domain(raw_domain: str) -> str:
        """Sanitize domain string by removing protocols, paths, ports, and trailing dots."""
        if not raw_domain or not isinstance(raw_domain, str):
            return ""

        domain = raw_domain.strip().lower()

        # Remove http:// or https:// prefix
        domain = re.sub(r"^https?://", "", domain)

        # Strip path, query params, port, and trailing dots
        domain = domain.split("/")[0].split("?")[0].split(":")[0].rstrip(".")

        return domain

    def query_record(self, domain: str, record_type: str) -> Dict[str, Any]:
        """Query a single DNS record type safely without raising unhandled exceptions.

        Returns a dictionary containing:
        - records: list of string representations of the records
        - error: descriptive error message string if failed, else None
        """
        try:
            answers = self.resolver.resolve(domain, record_type)
            records = []
            for rdata in answers:
                if record_type == "MX":
                    records.append(f"{rdata.preference} {rdata.exchange.to_text().rstrip('.')}")
                elif record_type in ("NS", "CNAME"):
                    records.append(rdata.target.to_text().rstrip("."))
                elif record_type == "TXT":
                    text_parts = [
                        part.decode("utf-8", errors="replace") if isinstance(part, bytes) else str(part)
                        for part in rdata.strings
                    ]
                    records.append("".join(text_parts))
                else:
                    records.append(rdata.to_text())
            return {"records": records, "error": None}

        except dns.resolver.NXDOMAIN:
            return {"records": [], "error": "NXDOMAIN: Domain does not exist"}
        except dns.resolver.NoAnswer:
            # Valid domain, but no record of this specific type exists (Normal DNS behavior)
            return {"records": [], "error": None}
        except dns.resolver.NoNameservers:
            logger.warning(f"No nameservers replied for domain '{domain}' record type '{record_type}'")
            return {"records": [], "error": "No nameservers replied to the query"}
        except dns.resolver.Timeout:
            logger.warning(f"DNS query timed out for domain '{domain}' record type '{record_type}'")
            return {"records": [], "error": f"Query timed out for {record_type} record"}
        except dns.exception.DNSException as exc:
            logger.warning(f"DNS exception for domain '{domain}' record type '{record_type}': {exc}")
            return {"records": [], "error": f"DNS resolution error: {str(exc)}"}
        except Exception as exc:
            logger.error(f"Unexpected error during DNS query for '{domain}' ({record_type}): {exc}")
            return {"records": [], "error": "Unexpected lookup error"}

    def analyze_domain(self, raw_domain: str) -> Dict[str, Any]:
        """Perform a complete DNS analysis for a domain.

        A single failed record lookup does NOT fail the entire analysis.
        Returns structured dictionary with:
        - domain: normalized domain name
        - is_resolvable: boolean flag
        - status: HEALTHY | DEGRADED | UNRESOLVABLE | INVALID
        - records: dict of record lists by type
        - errors: dict of any record-specific errors
        - response_time_ms: total lookup latency in ms
        """
        domain = self.sanitize_domain(raw_domain)

        if not domain:
            return {
                "domain": raw_domain,
                "is_resolvable": False,
                "status": "INVALID",
                "records": {rtype: [] for rtype in RECORD_TYPES},
                "errors": {"domain": "Invalid domain name provided"},
                "response_time_ms": 0.0,
            }

        start_time = time.perf_counter()
        records_result: Dict[str, List[str]] = {}
        errors_result: Dict[str, str] = {}

        is_nxdomain = False

        for rtype in RECORD_TYPES:
            query_res = self.query_record(domain, rtype)
            records_result[rtype] = query_res["records"]
            if query_res["error"]:
                errors_result[rtype] = query_res["error"]
                if "NXDOMAIN" in query_res["error"]:
                    is_nxdomain = True

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Determine overall domain resolvability & health status
        has_a_or_aaaa = bool(records_result.get("A") or records_result.get("AAAA") or records_result.get("CNAME"))
        has_ns = bool(records_result.get("NS"))

        if is_nxdomain:
            is_resolvable = False
            status = "UNRESOLVABLE"
        elif has_a_or_aaaa and has_ns:
            is_resolvable = True
            status = "HEALTHY"
        elif has_a_or_aaaa or has_ns:
            is_resolvable = True
            status = "DEGRADED"
        else:
            is_resolvable = False
            status = "UNRESOLVABLE"

        return {
            "domain": domain,
            "is_resolvable": is_resolvable,
            "status": status,
            "records": records_result,
            "errors": errors_result,
            "response_time_ms": elapsed_ms,
        }
