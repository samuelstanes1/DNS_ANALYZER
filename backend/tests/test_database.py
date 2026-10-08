"""Unit tests for MongoDB database layer and document schema."""

import os
from datetime import datetime
import pytest
from mongomock_motor import AsyncMongoMockClient

from app.database.mongodb import MongoDBManager, get_db_manager, get_analysis_collection
from app.models.analysis import DNSAnalysisDocument


@pytest.mark.anyio
async def test_analysis_document_structure():
    """Verify DNSAnalysisDocument schema fields and serialization."""
    doc = DNSAnalysisDocument(
        domain="example.com",
        status="HEALTHY",
        dns_analysis={
            "records": {"A": ["93.184.216.34"]},
            "errors": {},
            "response_time_ms": 12.5,
        },
    )

    assert doc.domain == "example.com"
    assert doc.status == "HEALTHY"
    assert doc.analysis_id is not None
    assert isinstance(doc.created_at, datetime)
    assert doc.dns_analysis["records"]["A"] == ["93.184.216.34"]

    mongo_dict = doc.to_mongo_dict()
    assert mongo_dict["analysis_id"] == doc.analysis_id
    assert mongo_dict["domain"] == "example.com"
    assert mongo_dict["status"] == "HEALTHY"


@pytest.mark.anyio
async def test_mongodb_manager_no_url():
    """Verify that manager returns False when MONGODB_URL is not set."""
    manager = MongoDBManager()
    connected = await manager.connect(mongodb_url="")
    assert connected is False
    assert manager.client is None
    assert manager.get_analysis_collection() is None


@pytest.mark.anyio
async def test_mongodb_mock_operations():
    """Verify database connection, ping, collection retrieval, and insertion using mock."""
    manager = MongoDBManager()
    
    # Use in-memory mock client for testing
    mock_client = AsyncMongoMockClient()
    manager.client = mock_client
    manager.db = mock_client["dns_health"]

    # Test collection access
    collection = manager.get_analysis_collection()
    assert collection is not None

    # Test inserting an analysis document
    sample_doc = DNSAnalysisDocument(
        domain="test.com",
        status="HEALTHY",
        dns_analysis={"records": {"A": ["1.2.3.4"]}},
    )
    insert_result = await collection.insert_one(sample_doc.to_mongo_dict())
    assert insert_result.inserted_id is not None

    # Test retrieving the document
    found = await collection.find_one({"analysis_id": sample_doc.analysis_id})
    assert found is not None
    assert found["domain"] == "test.com"
    assert found["status"] == "HEALTHY"

    # Test cleanup
    await manager.close()
    assert manager.client is None
    assert manager.db is None
