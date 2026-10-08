"""Pydantic schemas and document structures for DNS Analysis."""

from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field, field_validator


# RFC 1035 / RFC 1123 compliant label and domain validation
LABEL_REGEX = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")
TLD_REGEX = re.compile(r"^[a-zA-Z]{2,63}$")


class AnalysisCreateRequest(BaseModel):
    """Request schema for initiating domain DNS health analysis."""

    domain: str = Field(
        ...,
        description="Domain name to analyze (e.g. google.com or sub.example.org)",
        examples=["google.com"],
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_name(cls, v: str) -> str:
        """Validate, normalize, and clean the domain input."""
        if not v or not isinstance(v, str):
            raise ValueError("Domain must be a non-empty string.")

        cleaned = v.strip().lower()

        # Remove http:// or https:// prefix if present
        cleaned = re.sub(r"^https?://", "", cleaned)

        # Remove path, query string, port, and trailing dot
        cleaned = cleaned.split("/")[0].split("?")[0].split(":")[0].rstrip(".")

        if not cleaned:
            raise ValueError("Domain cannot be empty.")

        if len(cleaned) > 253:
            raise ValueError("Domain length must not exceed 253 characters.")

        if ".." in cleaned:
            raise ValueError(f"Invalid domain format: '{cleaned}' contains consecutive dots.")

        labels = cleaned.split(".")
        if len(labels) < 2:
            raise ValueError(f"Invalid domain format: '{cleaned}'. Domain must contain a valid name and TLD (e.g., example.com).")

        # Validate each individual label
        for label in labels:
            if not label:
                raise ValueError(f"Invalid domain format: '{cleaned}' contains empty labels.")
            if len(label) > 63:
                raise ValueError(f"Domain label '{label}' exceeds maximum allowed length of 63 characters.")
            if not LABEL_REGEX.match(label):
                raise ValueError(
                    f"Domain label '{label}' is invalid. Labels must start and end with an alphanumeric character and contain only letters, numbers, or hyphens."
                )

        # Validate top-level domain (TLD)
        tld = labels[-1]
        if not TLD_REGEX.match(tld):
            raise ValueError(f"Invalid top-level domain (TLD): '{tld}'. TLD must consist of 2 to 63 letters.")

        return cleaned


class AnalysisCreateResponse(BaseModel):
    """Response schema returned after initiating and storing DNS analysis."""

    analysis_id: str
    domain: str
    status: str = "completed"
    health_status: Optional[str] = None
    created_at: datetime


class AnalysisDetailResponse(BaseModel):
    """Detailed response schema returned when fetching an analysis by ID."""

    analysis_id: str
    domain: str
    status: str
    dns_analysis: Dict[str, Any]
    created_at: datetime


class DNSAnalysisDocument(BaseModel):
    """MongoDB Document schema for storing DNS Health Analysis results."""

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    status: str  # HEALTHY | DEGRADED | UNRESOLVABLE | INVALID
    dns_analysis: Dict[str, Any]  # Records, errors, latency, resolvability
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert document model to a dictionary suitable for MongoDB insertion."""
        return {
            "analysis_id": self.analysis_id,
            "domain": self.domain,
            "status": self.status,
            "dns_analysis": self.dns_analysis,
            "created_at": self.created_at,
        }
