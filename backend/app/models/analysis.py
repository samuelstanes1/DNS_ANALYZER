"""Pydantic schemas and document structures for DNS Analysis."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class DNSAnalysisDocument(BaseModel):
    """MongoDB Document schema for storing DNS Health Analysis results."""

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    status: str  # e.g. HEALTHY, DEGRADED, UNRESOLVABLE, INVALID
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
