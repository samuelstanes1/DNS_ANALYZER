# DNS Health Analyzer 🔍

> **Interview Submission Project**: A production-grade, full-stack DNS Health Diagnostics & Intelligence application built with **FastAPI**, **MongoDB**, **dnspython**, and a modern **React (TypeScript + Vite + Tailwind CSS)** dashboard.

---

## 📋 Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Problem Statement](#2-problem-statement)
- [3. Features](#3-features)
- [4. Architecture Overview](#4-architecture-overview)
- [5. Technology Stack](#5-technology-stack)
- [6. Project Directory Structure](#6-project-directory-structure)
- [7. Backend Setup & Installation](#7-backend-setup--installation)
- [8. MongoDB Database Configuration](#8-mongodb-database-configuration)
- [9. Frontend Setup & Installation](#9-frontend-setup--installation)
- [10. Running the Application](#10-running-the-application)
- [11. API Documentation & Endpoints](#11-api-documentation--endpoints)
- [12. DNS Analysis Engine & Health Logic](#12-dns-analysis-engine--health-logic)
- [13. Testing Suite & Test Instructions](#13-testing-suite--test-instructions)
- [14. Git Commit History & Implementation Phases](#14-git-commit-history--implementation-phases)
- [15. End-to-End Execution Flow](#15-end-to-end-execution-flow)
- [16. Known Limitations](#16-known-limitations)
- [17. Future Improvements](#17-future-improvements)

---

## 1. Project Overview

**DNS Health Analyzer** is a clean, modular developer tool that diagnoses the DNS configuration and operational health of any internet domain. It queries core DNS record types, measures resolution latency, determines domain resolvability, safely persists immutable audit reports to **MongoDB**, and serves analysis via REST APIs and an intuitive web dashboard.

---

## 2. Problem Statement

DNS misconfigurations (such as missing MX records, missing nameservers, broken IPv6 AAAA configurations, or expired domain pointers) are among the leading causes of service downtime, delivery failure in enterprise emails, and routing latency. 

Developers and system administrators need a lightweight, reliable, and decoupled tool that:
1. Performs non-destructive, isolated DNS diagnostics across multiple record types simultaneously.
2. Gracefully handles lookup timeouts, non-existent domains, and missing record types without cascading application failures.
3. Persists diagnostic snapshots with unique UUIDs for historical audit, sharing, and lookup.

---

## 3. Features

- **Multi-Record DNS Diagnostics**: Analyzes `A`, `AAAA`, `MX`, `NS`, `TXT`, and `CNAME` records in isolated query steps.
- **Per-Record Fault Isolation**: A timeout or failure on one record type (e.g. `TXT`) never crashes or invalidates the rest of the domain analysis.
- **RFC 1035 / 1123 Domain Sanitization**: Strips URL protocols (`http://`, `https://`), paths, query strings, and validates label constraints (length, hyphens, alphanumeric characters).
- **Asynchronous Persistence**: Uses **Motor** (async MongoDB driver) to store non-blocking analysis reports.
- **RESTful API**: Fast and fully documented OpenAPI/Swagger endpoints.
- **Zero Information Leakage**: Sanitized exception handlers ensure database connection strings and raw stack traces are never exposed to API consumers.
- **Developer Dashboard**: Single-page light-themed UI with real-time API health polling, one-click analysis ID copying, and responsive record tables.
- **100% Deterministic Test Suite**: 28 isolated unit/API tests with mocked DNS resolution and MongoDB in-memory mocking (< 1 second execution).

---

## 4. Architecture Overview

The system follows a strict **Layered Clean Architecture**:

```text
┌─────────────────────────────────────────────────────────────┐
│               Frontend (React + TS + Tailwind)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Routing Layer                    │
│      (CORS, Request Validation, Global Exception Handlers)  │
├──────────────────────────────┬──────────────────────────────┤
│               Service Layer  │      Repository Layer        │
│        (DNSAnalyzerService)  │    (AnalysisRepository)      │
├──────────────────────────────┼──────────────────────────────┤
│      dnspython Engine        │   Motor Async MongoDB Driver │
│     (Public Resolvers)       │     (MongoDB Atlas / Local)  │
└──────────────────────────────┴──────────────────────────────┘
```

- **API Route Layer** (`app/api/`): Thin controllers that coordinate request validation, service execution, and response schemas.
- **Data Models** (`app/models/`): Pydantic v2 schemas defining input validation rules, output contracts, and MongoDB document structures.
- **Services Layer** (`app/services/`): Pure DNS diagnostic logic decoupled from HTTP and database frameworks.
- **Database Layer** (`app/database/`): Asynchronous Motor client lifecycle management and repository pattern abstractions.

---

## 5. Technology Stack

### Backend
- **Language**: Python 3.9+ / Python 3.10+
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous ASGI Web Framework)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **DNS Resolution Engine**: [dnspython](https://www.dnspython.org/)
- **Database Driver**: [Motor](https://motor.readthedocs.io/) & [PyMongo](https://pymongo.readthedocs.io/)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/) & `python-dotenv`
- **SSL / TLS Negotiation**: `certifi` (Secure Atlas CA trust store)

### Frontend
- **Framework**: [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)

### Database
- **MongoDB**: Document database (MongoDB Community 7.0+ or MongoDB Atlas Cloud)

### Testing
- `pytest` (8.x)
- `pytest-anyio` / `anyio` (async test execution)
- `httpx` (FastAPI ASGI transport client)
- `mongomock-motor` (in-memory async database mocking)

---

## 6. Project Directory Structure

```text
DNS_ANALYZER/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py              # POST /analysis & GET /analysis/{id}
│   │   ├── database/
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   └── analysis_repo.py     # Database queries & projection
│   │   │   ├── __init__.py
│   │   │   ├── check_connection.py      # CLI connection verification tool
│   │   │   └── mongodb.py               # Asynchronous Motor client manager
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py              # Pydantic models & domain validation
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── dns_service.py           # Isolated dnspython diagnostic engine
│   │   ├── __init__.py
│   │   └── main.py                      # FastAPI entry point, CORS & lifespan
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api_analysis.py         # API integration tests (POST & GET)
│   │   ├── test_database.py             # MongoDB manager & document tests
│   │   └── test_dns_service.py          # Deterministic DNS resolution tests
│   ├── .env.example                     # Environment template
│   └── requirements.txt                 # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx                      # Main DNS Health Dashboard component
│   │   ├── index.css                    # Tailwind setup & badge styles
│   │   └── main.tsx                     # React root bootstrap
│   ├── .env.example                     # Frontend environment template
│   ├── index.html                       # HTML template (Inter + JetBrains Mono)
│   ├── package.json                     # Frontend dependencies
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── .gitignore                           # Comprehensive git ignore rules
└── README.md                            # Complete project documentation
```

---

## 7. Backend Setup & Installation

### Prerequisites
- Python 3.9+ (Python 3.9.6+ or Python 3.10+ recommended)
- `pip` package manager

### 1. Navigate to the backend directory
```bash
cd backend
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 8. MongoDB Database Configuration

### 1. Environment Variable Setup
Copy the `.env.example` template into `backend/.env`:
```bash
cp .env.example .env
```

Edit `backend/.env`:
```env
# Connection String (Local MongoDB or MongoDB Atlas)
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=dns_health

# Application Settings
APP_NAME=DNS Health Analyzer
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1
```

> **Security Note**: The `.env` file is excluded from Git tracking via `.gitignore`. No credentials or connection strings are hardcoded in the source code.

### 2. Options for Running MongoDB
- **Option A (MongoDB Atlas Free M0 Tier - Recommended)**: Create a free cluster on [mongodb.com/atlas](https://www.mongodb.com/atlas), allow Network Access from anywhere (`0.0.0.0/0`), and copy the connection string.
- **Option B (Local macOS Homebrew)**:
  ```bash
  brew tap mongodb/brew
  brew install mongodb-community
  brew services start mongodb-community
  # Set MONGODB_URL=mongodb://localhost:27017
  ```
- **Option C (Docker)**:
  ```bash
  docker run -d --name mongodb -p 27017:27017 mongo:latest
  ```

### 3. Verify MongoDB Connection
Run the built-in diagnostic script:
```bash
python -m app.database.check_connection
```
Expected output:
```text
==================================================
DNS Health Analyzer - MongoDB Connectivity Test
==================================================
Target Database: dns_health
MongoDB URL Configured: YES

Attempting connection to MongoDB...
[✓] Successfully connected to MongoDB!
[✓] Ping check: PASSED
[✓] Analysis Collection 'analyses' is ready.
==================================================
```

---

## 9. Frontend Setup & Installation

### Prerequisites
- Node.js (v18+ or v20+)
- `npm`

### 1. Navigate to the frontend directory
```bash
cd frontend
```

### 2. Install dependencies
```bash
npm install
```

### 3. Configure Frontend Environment
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 10. Running the Application

### Terminal 1: Start FastAPI Backend Server
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Alternative Redoc UI: `http://127.0.0.1:8000/redoc`

### Terminal 2: Start Frontend Development Server
```bash
cd frontend
npm run dev
```
- Dashboard URL: `http://localhost:5173`

---

## 11. API Documentation & Endpoints

### Summary Table

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root verification endpoint | `200 OK` |
| `GET` | `/health` | Backend and MongoDB health check | `200 OK` |
| `POST` | `/analysis` | Initiates DNS analysis and stores report | `201 Created` |
| `GET` | `/analysis/{analysis_id}` | Retrieves full stored analysis report by ID | `200 OK` / `404 Not Found` |

---

### Endpoint 1: `POST /analysis`

**Purpose**: Accepts a domain name, normalizes and validates the domain format, executes DNS lookups for all supported record types, saves the document to MongoDB, and returns a summary.

#### Request Example:
```bash
curl -X POST http://127.0.0.1:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

#### Success Response (`201 Created`):
```json
{
  "analysis_id": "7f059052-413b-4a89-8d6c-f79bcfe2f9c2",
  "domain": "google.com",
  "status": "completed",
  "health_status": "HEALTHY",
  "created_at": "2026-10-08T19:57:29.955628Z"
}
```

#### Error Responses:
- **`422 Unprocessable Entity` (Invalid Domain / Missing Field)**:
  ```json
  {
    "detail": "domain: Invalid domain format: 'invalid_domain..com'. Please provide a valid domain name (e.g., example.com)."
  }
  ```
- **`503 Service Unavailable` (MongoDB Connection Failure)**:
  ```json
  {
    "detail": "Database storage is currently unavailable."
  }
  ```

---

### Endpoint 2: `GET /analysis/{analysis_id}`

**Purpose**: Fetches a stored DNS diagnostic document from MongoDB using its UUID without exposing MongoDB internal `_id` fields.

#### Request Example:
```bash
curl -X GET http://127.0.0.1:8000/analysis/7f059052-413b-4a89-8d6c-f79bcfe2f9c2
```

#### Success Response (`200 OK`):
```json
{
  "analysis_id": "7f059052-413b-4a89-8d6c-f79bcfe2f9c2",
  "domain": "google.com",
  "status": "HEALTHY",
  "dns_analysis": {
    "domain": "google.com",
    "is_resolvable": true,
    "status": "HEALTHY",
    "records": {
      "A": ["142.250.190.46"],
      "AAAA": ["2404:6800:4009:826::200e"],
      "MX": ["10 smtp.google.com"],
      "NS": ["ns1.google.com", "ns2.google.com", "ns3.google.com", "ns4.google.com"],
      "TXT": ["v=spf1 include:_spf.google.com ~all"],
      "CNAME": []
    },
    "errors": {},
    "response_time_ms": 32.5
  },
  "created_at": "2026-10-08T19:57:29.955000Z"
}
```

#### Not Found Response (`404 Not Found`):
```json
{
  "detail": "Analysis with ID 'non-existent-id' was not found."
}
```

---

### Endpoint 3: `GET /health`

**Purpose**: Verifies that the API server is alive and tests MongoDB connection health via a live database ping.

```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## 12. DNS Analysis Engine & Health Logic

The DNS Engine is isolated inside [`app/services/dns_service.py`](file:///Users/shivaninavaneethan/Documents/Shivani/DNS_ANALYZER/backend/app/services/dns_service.py).

### Record Types Analyzed
- **`A`**: IPv4 address routing
- **`AAAA`**: IPv6 address routing
- **`MX`**: Mail exchange servers and delivery priority
- **`NS`**: Authoritative name servers
- **`TXT`**: Domain ownership, SPF, DKIM, and security verifications
- **`CNAME`**: Canonical alias mapping

### Health Classification Criteria
- **`HEALTHY`**: Domain resolves successfully, has at least one valid routing record (`A`, `AAAA`, or `CNAME`), and has authoritative `NS` records.
- **`DEGRADED`**: Domain resolves partially (e.g. has address records but no nameservers answered directly).
- **`UNRESOLVABLE`**: Domain returned `NXDOMAIN` (does not exist) or all queries timed out without answers.
- **`INVALID`**: Domain input failed sanitization or contains illegal syntax.

---

## 13. Testing Suite & Test Instructions

The test suite is built on **pytest** and designed to be **100% deterministic, offline-capable, and fast**. External DNS calls and live MongoDB instances are isolated using `unittest.mock` and `mongomock-motor`.

### Run All Tests
```bash
cd backend
pytest -v
```

### Test Suite Output
```text
============================== test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/shivaninavaneethan/Documents/Shivani/DNS_ANALYZER/backend

tests/test_api_analysis.py::test_start_dns_analysis_valid_request[asyncio] PASSED [  3%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-invalid_domain..com] PASSED [  7%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-google] PASSED [ 10%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio--startwithhyphen.com] PASSED [ 14%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-endwithhyphen-.com] PASSED [ 17%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-test.c0m] PASSED [ 21%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-long_label.com] PASSED [ 25%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-empty] PASSED [ 28%]
tests/test_api_analysis.py::test_start_dns_analysis_invalid_domain_variations[asyncio-whitespace] PASSED [ 32%]
tests/test_api_analysis.py::test_start_dns_analysis_missing_domain[asyncio] PASSED [ 35%]
tests/test_api_analysis.py::test_start_dns_analysis_malformed_payload[asyncio] PASSED [ 39%]
tests/test_api_analysis.py::test_start_dns_analysis_db_unavailable[asyncio] PASSED [ 42%]
tests/test_api_analysis.py::test_get_analysis_existing_id[asyncio] PASSED [ 46%]
tests/test_api_analysis.py::test_get_analysis_non_existing_id[asyncio] PASSED [ 50%]
tests/test_api_analysis.py::test_get_analysis_db_unavailable[asyncio] PASSED [ 53%]
tests/test_api_analysis.py::test_full_analysis_workflow_post_then_get[asyncio] PASSED [ 57%]
tests/test_database.py::test_analysis_document_structure[asyncio] PASSED [ 60%]
tests/test_database.py::test_mongodb_manager_no_url[asyncio] PASSED      [ 64%]
tests/test_database.py::test_mongodb_mock_operations[asyncio] PASSED     [ 67%]
tests/test_dns_service.py::test_sanitize_domain PASSED                   [ 71%]
tests/test_dns_service.py::test_analyze_empty_or_invalid_domain PASSED   [ 75%]
tests/test_dns_service.py::test_successful_dns_lookup_all_records PASSED [ 78%]
tests/test_dns_service.py::test_missing_record_types_handling PASSED     [ 82%]
tests/test_dns_service.py::test_failed_dns_lookup_nxdomain PASSED        [ 85%]
tests/test_dns_service.py::test_single_failed_record_does_not_fail_entire_analysis PASSED [ 89%]
tests/test_dns_service.py::test_failed_dns_lookup_timeout PASSED         [ 92%]
tests/test_dns_service.py::test_failed_dns_lookup_no_nameservers PASSED  [ 96%]
tests/test_dns_service.py::test_failed_dns_lookup_generic_exception PASSED [100%]

======================= 28 passed in 0.85s ========================
```

---

## 14. Git Commit History & Implementation Phases

The project was engineered iteratively through structured phases following professional Git discipline:

```text
* 245baeb - feat: add DNS health dashboard (Phase 9)
* ad4889c - test: expand backend test coverage (Phase 8)
* eaa484b - fix: improve validation and error handling (Phase 7)
* aff5285 - feat: add analysis result retrieval (Phase 6)
* 040ca85 - feat: implement DNS analysis endpoint (Phase 5)
* 3f60560 - feat: integrate MongoDB storage (Phase 4)
* 5229f78 - feat: implement DNSAnalyzerService and pytest test suite (Phase 3)
* 540a733 - feat(backend): setup minimal fastapi app with health check (Phase 2)
* d1220b2 - chore: initialize project structure (Phase 1)
```

---

## 15. End-to-End Execution Flow

```text
  [ User / Web Dashboard ]
             │
             │  1. POST /analysis {"domain": "google.com"}
             ▼
  [ FastAPI Route Controller ]
             │
             │  2. Sanitize & Validate (RFC 1035/1123)
             ▼
  [ DNSAnalyzerService ] ───► Queries DNS (A, AAAA, MX, NS, TXT, CNAME)
             │
             │  3. Formulates DNSAnalysisDocument (UUID, Status, Records, Latency)
             ▼
  [ AnalysisRepository ]
             │
             │  4. Inserts into MongoDB 'analyses' collection
             ▼
  [ MongoDB Database ]
             │
             │  5. Returns analysis_id (e.g. 7f059052-...)
             ▼
  [ Frontend Dashboard ]
             │
             │  6. GET /analysis/{analysis_id}
             ▼
  [ Instant Diagnostic Render (Badges, Records, Latency) ]
```

---

## 16. Known Limitations

1. **Synchronous Query Execution per Request**: DNS lookups are currently executed in an isolated thread pool; high volume concurrent requests would benefit from an asynchronous background task queue (e.g. Celery or ARQ).
2. **Standard Public Resolvers**: Queries use configured public upstream resolvers (Google `8.8.8.8` / Cloudflare `1.1.1.1`). Recursive authoritative traversal from root DNS servers is not implemented in this version.
3. **No Historical List / Pagination Endpoint**: Results are retrieved on-demand via unique analysis IDs (`/analysis/{id}`). A paginated `/analyses` listing endpoint is omitted to keep the interview scope focused and lightweight.

---

## 17. Future Improvements

- **Redis Cache Layer**: Cache repetitive domain queries with short TTLs (e.g. 60 seconds) to reduce upstream nameserver query traffic.
- **DNSSEC & CAA Record Verification**: Add cryptographic DNSSEC chain verification and Certificate Authority Authorization (CAA) diagnostics.
- **Background Worker Queue**: Offload high-latency lookups to Celery / Redis worker queues with WebSocket real-time progress updates.
- **Export Capabilities**: Add 1-click JSON and PDF compliance report export from the web dashboard.
- **Historical Trends & Uptime Monitoring**: Recurring cron schedules to track DNS record drift and DNS latency over time.
