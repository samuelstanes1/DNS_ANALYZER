"""API tests for POST /analysis endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.database.mongodb import db_manager


@pytest.fixture(autouse=True)
def setup_mock_db():
    """Ensure in-memory mock database is used for API tests."""
    mock_client = AsyncMongoMockClient()
    db_manager.client = mock_client
    db_manager.db = mock_client["dns_health"]
    yield
    db_manager.client = None
    db_manager.db = None


@pytest.mark.anyio
async def test_start_dns_analysis_valid_request():
    """Test POST /analysis with a valid domain."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={"domain": "google.com"})

    assert response.status_code == 201
    data = response.json()
    assert "analysis_id" in data
    assert data["domain"] == "google.com"
    assert data["status"] == "completed"
    assert data["health_status"] in ("HEALTHY", "DEGRADED", "UNRESOLVABLE")
    assert "created_at" in data

    # Verify that the document is saved in MongoDB mock collection
    collection = db_manager.get_analysis_collection()
    doc = await collection.find_one({"analysis_id": data["analysis_id"]})
    assert doc is not None
    assert doc["domain"] == "google.com"
    assert "records" in doc["dns_analysis"]


@pytest.mark.anyio
async def test_start_dns_analysis_invalid_domain():
    """Test POST /analysis with an invalid domain string."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={"domain": "invalid_domain..com"})

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_start_dns_analysis_missing_domain():
    """Test POST /analysis with missing domain field."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={})

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_start_dns_analysis_malformed_payload():
    """Test POST /analysis with malformed data types."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={"domain": None})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_start_dns_analysis_db_unavailable():
    """Test POST /analysis handles database failure gracefully without exposing stack trace."""
    # Force db collection to be None to simulate unavailable DB
    db_manager.db = None
    db_manager.client = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={"domain": "google.com"})

    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Database storage is currently unavailable."
