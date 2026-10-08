# DNS Health Analyzer

> **Note**: This project is developed as a backend interview demonstration project, focusing on clean architecture, asynchronous Python backend patterns, MongoDB persistence, and straightforward domain DNS diagnostic reporting.

---

## 📌 Project Overview

**DNS Health Analyzer** is a lightweight, high-performance web application designed to evaluate the health, status, and records of domain names. It performs multi-record DNS diagnostics (such as A, AAAA, MX, NS, TXT, CNAME, SOA), calculates overall health metrics, stores analysis results asynchronously in MongoDB, and provides immediate as well as historical lookup capabilities via REST APIs.

---

## 🛠 Planned Technologies

- **Backend**:
  - **Framework**: Python 3.10+ with [FastAPI](https://fastapi.tiangolo.com/) (Async ASGI framework)
  - **Server**: [Uvicorn](https://www.uvicorn.org/)
  - **DNS Resolution Engine**: `dnspython` / `aiodns` for non-blocking asynchronous DNS queries
  - **Database Driver**: `motor` (Asynchronous MongoDB driver for Python) / PyMongo
  - **Data Validation & Settings**: Pydantic v2 & `pydantic-settings`
- **Database**:
  - **MongoDB**: Document database for persisting detailed DNS analysis records, health summaries, and query timestamps
- **Frontend**:
  - Clean, modern, light-themed Vanilla HTML5, CSS3, and JavaScript
  - Responsive single-page dashboard with real-time status indication

---

## 📁 Planned Project Structure

```text
dns-health-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── analysis.py       # Analysis trigger & retrieval endpoints
│   │   │       │   └── health.py         # Service health check endpoint
│   │   │       └── router.py             # API v1 central router
│   │   ├── core/
│   │   │   ├── config.py                 # Environment and application configuration
│   │   │   └── logging.py                # Logging setup
│   │   ├── db/
│   │   │   ├── mongodb.py                # MongoDB connection management (Motor)
│   │   │   └── repositories/
│   │   │       └── analysis_repo.py      # Database operations for analysis results
│   │   ├── models/
│   │   │   ├── domain.py                 # Domain and record data models
│   │   │   └── analysis.py               # Pydantic schemas for requests & responses
│   │   ├── services/
│   │   │   ├── dns_service.py            # DNS query execution & resolver logic
│   │   │   └── health_evaluator.py       # Logic for overall health computation
│   │   └── main.py                       # FastAPI application entry point
│   ├── requirements.txt                  # Python dependency specifications
│   └── .env.example                      # Example environment variables
├── frontend/
│   ├── index.html                        # Dashboard HTML structure
│   ├── styles.css                        # Light-themed, modern styling
│   └── app.js                            # Frontend API interaction and state handling
├── .gitignore                            # Git ignore rules for Python, Node, IDEs & env
└── README.md                             # Project documentation
```

---

## 🔌 Planned API Endpoints

1. **Start DNS Analysis**
   - **Endpoint**: `POST /api/v1/analyze`
   - **Description**: Accepts a target domain, performs DNS queries, evaluates domain health, saves results to MongoDB, and returns the analysis summary with a unique analysis ID.

2. **Retrieve Analysis Result**
   - **Endpoint**: `GET /api/v1/analysis/{analysis_id}`
   - **Description**: Fetches an existing DNS analysis report from MongoDB using its unique ID.

3. **System Health Check**
   - **Endpoint**: `GET /api/v1/health`
   - **Description**: Verifies backend and MongoDB connectivity status.

---

## 🎨 Planned UI Design (Light Theme)

```text
┌──────────────────────────────────────────────────────────┐
│  DNS Health                                    ● Online  │
│  Domain intelligence & DNS diagnostics                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Analyze a domain                                        │
│  ┌──────────────────────────────────────────┐ ┌────────┐ │
│  │ Enter domain e.g. google.com             │ │ Analyze│ │
│  └──────────────────────────────────────────┘ └────────┘ │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  DNS Health                                               │
│                                                          │
│       ● HEALTHY                                          │
│                                                          │
│  Domain        google.com                                │
│  Analysis ID   8f92...                                   │
│                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ A       │  │ AAAA    │  │ MX      │  │ NS      │     │
│  │ ✓       │  │ ✓       │  │ ✓       │  │ ✓       │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│                                                          │
│  DNS Records                                             │
│  ──────────────────────────────────────────────────────  │
│  A       142.xxx.xxx.xxx                                 │
│  MX      mail.google.com                                 │
│  NS      ns1.google.com                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
