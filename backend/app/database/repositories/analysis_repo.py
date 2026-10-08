"""Repository layer for Analysis database interactions."""

from typing import Any, Dict, Optional
from app.database.mongodb import get_analysis_collection
from app.models.analysis import DNSAnalysisDocument


class AnalysisRepository:
    """Encapsulates all database operations for DNS analysis records."""

    @staticmethod
    async def insert_analysis(document: DNSAnalysisDocument) -> None:
        """Insert a new DNS analysis document into MongoDB."""
        collection = get_analysis_collection()
        if collection is None:
            raise RuntimeError("Database collection is not available.")
        await collection.insert_one(document.to_mongo_dict())

    @staticmethod
    async def find_by_analysis_id(analysis_id: str) -> Optional[Dict[str, Any]]:
        """Find an analysis document by its unique analysis_id, excluding MongoDB _id."""
        collection = get_analysis_collection()
        if collection is None:
            raise RuntimeError("Database collection is not available.")

        # Project out MongoDB internal _id field
        doc = await collection.find_one(
            {"analysis_id": analysis_id},
            {"_id": 0},
        )
        return doc
