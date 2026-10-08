"""Pydantic schemas and document structures for DNS Analysis."""

from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field, field_validator


DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)


class AnalysisCreateRequest(BaseModel):
    """Request schema for initiating domain DNS health analysis."""

    domain: str = Field(
        ...,
        description="Domain name to analyze, e.g., google.com or sub.example.org",
        examples=["google.com"],
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_name(cls, v: str) -> str:
        """Validate and clean the domain input."""
        if not v or not isinstance(v, str):
            raise ValueError("Domain must be a non-empty string.")

        cleaned = v.strip().lower()
        # Remove http:// or https:// if provided
        cleaned = re.sub(r"^https?://", "", cleaned)
        # Remove path, port, or query string
        cleaned = cleaned.split("/")[0].split("?")[0].split(":")[0].rstrip(".")

        if not cleaned:
            raise ValueError("Domain cannot be empty.")

        if len(cleaned) > 253:
            raise ValueError("Domain length must not exceed 253 characters.")

        if not DOMAIN_REGEX.match(cleaned):
            raise ValueError(f"Invalid domain format: '{cleaned}'. Please provide a valid domain name (e.g., example.com).")

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
