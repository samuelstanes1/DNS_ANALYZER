"""Analysis API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status
import pymongo.errors

from app.database.mongodb import get_analysis_collection
from app.models.analysis import AnalysisCreateRequest, AnalysisCreateResponse, DNSAnalysisDocument
from app.services.dns_service import DNSAnalyzerService

logger = logging.getLogger("dns_analyzer.api")

router = APIRouter(tags=["Analysis"])

# Service instance
dns_service = DNSAnalyzerService()


@router.post(
    "/analysis",
    response_model=AnalysisCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start DNS Analysis",
    description="Initiates DNS health analysis for a domain, evaluates records, and persists results.",
)
async def start_dns_analysis(request: AnalysisCreateRequest) -> AnalysisCreateResponse:
    """Coordinate DNS analysis and persistence for a requested domain."""
    # 1. Execute domain DNS health analysis
    try:
        dns_result = dns_service.analyze_domain(request.domain)
    except Exception as exc:
        logger.error(f"DNS Analysis execution error for domain {request.domain}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete DNS lookup analysis.",
        )

    # 2. Build analysis document
    document = DNSAnalysisDocument(
        domain=dns_result.get("domain", request.domain),
        status=dns_result.get("status", "UNKNOWN"),
        dns_analysis=dns_result,
    )

    # 3. Persist document to MongoDB
    collection = get_analysis_collection()
    if collection is None:
        logger.error("MongoDB collection not available during analysis storage.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database storage is currently unavailable.",
        )

    try:
        await collection.insert_one(document.to_mongo_dict())
    except pymongo.errors.PyMongoError as exc:
        logger.error(f"MongoDB persistence error for analysis {document.analysis_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to save analysis report to database.",
        )
    except Exception as exc:
        logger.error(f"Unexpected error while saving analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while saving the analysis.",
        )

    # 4. Return structured response
    return AnalysisCreateResponse(
        analysis_id=document.analysis_id,
        domain=document.domain,
        status="completed",
        health_status=document.status,
        created_at=document.created_at,
    )
