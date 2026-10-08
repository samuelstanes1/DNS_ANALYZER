"""API tests for POST /analysis and GET /analysis/{analysis_id} endpoints."""

from unittest.mock import patch
import pytest
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.database.mongodb import db_manager
from app.models.analysis import DNSAnalysisDocument


@pytest.fixture(autouse=True)
def setup_mock_db_and_dns():
    """Ensure in-memory mock database and mock DNS resolver are used for deterministic tests."""
    mock_client = AsyncMongoMockClient()
    db_manager.client = mock_client
    db_manager.db = mock_client["dns_health"]

    mock_dns_result = {
        "domain": "google.com",
        "is_resolvable": True,
        "status": "HEALTHY",
        "records": {
            "A": ["142.250.190.46"],
            "AAAA": ["2404:6800:4009:826::200e"],
            "MX": ["10 smtp.google.com"],
            "NS": ["ns1.google.com"],
            "TXT": ["v=spf1 include:_spf.google.com ~all"],
            "CNAME": [],
        },
        "errors": {},
        "response_time_ms": 25.4,
    }

    with patch("app.api.analysis.dns_service.analyze_domain", return_value=mock_dns_result):
        yield

    db_manager.client = None
    db_manager.db = None


# ---------------------------------------------------------------------------
# POST /analysis Tests
# ---------------------------------------------------------------------------


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
    assert data["health_status"] == "HEALTHY"
    assert "created_at" in data

    # Verify document in collection
    collection = db_manager.get_analysis_collection()
    doc = await collection.find_one({"analysis_id": data["analysis_id"]})
    assert doc is not None
    assert doc["domain"] == "google.com"
    assert "records" in doc["dns_analysis"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_domain",
    [
        "invalid_domain..com",       # Consecutive dots
        "google",                    # Missing TLD
        "-startwithhyphen.com",      # Label starts with hyphen
        "endwithhyphen-.com",        # Label ends with hyphen
        "test.c0m",                  # Number in TLD
        "a" * 64 + ".com",           # Label > 63 chars
        "",                          # Empty string
        "   ",                       # Whitespace only
    ],
)
async def test_start_dns_analysis_invalid_domain_variations(invalid_domain):
    """Test POST /analysis rejects various invalid domain formats with 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={"domain": invalid_domain})

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


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
    db_manager.db = None
    db_manager.client = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analysis", json={"domain": "google.com"})

    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Database storage is currently unavailable."
    assert "Traceback" not in str(data)


# ---------------------------------------------------------------------------
# GET /analysis/{analysis_id} Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_analysis_existing_id():
    """Test GET /analysis/{analysis_id} for an existing record."""
    sample_doc = DNSAnalysisDocument(
        analysis_id="test-analysis-123",
        domain="example.com",
        status="HEALTHY",
        dns_analysis={
            "domain": "example.com",
            "is_resolvable": True,
            "status": "HEALTHY",
            "records": {"A": ["93.184.216.34"], "NS": ["a.iana-servers.net."]},
            "errors": {},
            "response_time_ms": 15.2,
        },
    )
    collection = db_manager.get_analysis_collection()
    await collection.insert_one(sample_doc.to_mongo_dict())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analysis/test-analysis-123")

    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == "test-analysis-123"
    assert data["domain"] == "example.com"
    assert data["status"] == "HEALTHY"
    assert "dns_analysis" in data
    assert data["dns_analysis"]["records"]["A"] == ["93.184.216.34"]
    assert "_id" not in data


@pytest.mark.anyio
async def test_get_analysis_non_existing_id():
    """Test GET /analysis/{analysis_id} for a non-existent ID returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analysis/non-existent-uuid-999")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.anyio
async def test_get_analysis_db_unavailable():
    """Test GET /analysis/{analysis_id} handles DB unavailable cleanly."""
    db_manager.db = None
    db_manager.client = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/analysis/some-id")

    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Database storage is currently unavailable."


# ---------------------------------------------------------------------------
# End-to-End Flow Test (POST -> GET)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_full_analysis_workflow_post_then_get():
    """Verify complete flow: POST domain -> get analysis_id -> GET by analysis_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Initiate analysis
        post_res = await client.post("/analysis", json={"domain": "google.com"})
        assert post_res.status_code == 201
        post_data = post_res.json()
        analysis_id = post_data["analysis_id"]
        assert analysis_id is not None

        # 2. Retrieve analysis using generated ID
        get_res = await client.get(f"/analysis/{analysis_id}")
        assert get_res.status_code == 200
        get_data = get_res.json()

        assert get_data["analysis_id"] == analysis_id
        assert get_data["domain"] == "google.com"
        assert get_data["status"] == "HEALTHY"
        assert "dns_analysis" in get_data
        assert "A" in get_data["dns_analysis"]["records"]
        assert len(get_data["dns_analysis"]["records"]["A"]) > 0
