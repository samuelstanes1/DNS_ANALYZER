"""Analysis API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Path, status
import pymongo.errors

from app.database.repositories.analysis_repo import AnalysisRepository
from app.models.analysis import (
    AnalysisCreateRequest,
    AnalysisCreateResponse,
    AnalysisDetailResponse,
    DNSAnalysisDocument,
)
from app.services.dns_service import DNSAnalyzerService

logger = logging.getLogger("dns_analyzer.api")

router = APIRouter(tags=["Analysis"])

# Service instances
dns_service = DNSAnalyzerService()
analysis_repo = AnalysisRepository()


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

    # 3. Persist document via repository
    try:
        await analysis_repo.insert_analysis(document)
    except RuntimeError as exc:
        logger.error(f"Database availability error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database storage is currently unavailable.",
        )
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


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve DNS Analysis Result",
    description="Fetches stored DNS health analysis report and record diagnostics using the unique analysis ID.",
)
async def get_dns_analysis(
    analysis_id: str = Path(
        ...,
        description="Unique UUID string identifying the analysis",
        examples=["8f92-abcd-1234-5678"],
    )
) -> AnalysisDetailResponse:
    """Retrieve an existing DNS analysis document by analysis ID."""
    clean_id = analysis_id.strip()

    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis ID must not be empty.",
        )

    # Query repository for analysis document
    try:
        doc = await analysis_repo.find_by_analysis_id(clean_id)
    except RuntimeError as exc:
        logger.error(f"Database availability error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database storage is currently unavailable.",
        )
    except pymongo.errors.PyMongoError as exc:
        logger.error(f"Database query error for ID {clean_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database query failed while retrieving analysis.",
        )
    except Exception as exc:
        logger.error(f"Unexpected error retrieving analysis ID {clean_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the analysis.",
        )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{clean_id}' was not found.",
        )

    return AnalysisDetailResponse(
        analysis_id=doc["analysis_id"],
        domain=doc["domain"],
        status=doc.get("status", "UNKNOWN"),
        dns_analysis=doc.get("dns_analysis", {}),
        created_at=doc["created_at"],
    )
