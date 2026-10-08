"""DNS Health Analyzer FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis import router as analysis_router
from app.database.mongodb import db_manager

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger("dns_analyzer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle events."""
    logger.info("Initializing application and connecting to MongoDB...")
    connected = await db_manager.connect()
    if connected:
        logger.info("Successfully connected to MongoDB database.")
    else:
        logger.warning(
            "MongoDB not connected on startup. Database operations will return HTTP 503 until connection is established."
        )

    yield

    logger.info("Shutting down application and closing MongoDB connections...")
    await db_manager.close()


app = FastAPI(
    title="DNS Health Analyzer API",
    description="Backend service for DNS health diagnostics, record verification, and monitoring.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(analysis_router)


# ---------------------------------------------------------------------------
# Global Exception Handlers (Ensures zero exposure of internal tracebacks/secrets)
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format validation errors into clear, consistent messages."""
    errors = exc.errors()
    # Extract clean human-readable error messages
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{loc}: {msg}" if loc else msg)

    detail_message = "; ".join(error_messages) or "Invalid request payload."
    logger.warning(f"Request validation failed for {request.url.path}: {detail_message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail_message},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTPExceptions return standard structured JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions to prevent internal leakages."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Base Endpoints
# ---------------------------------------------------------------------------


@app.get("/", summary="Root Status")
def root():
    """Root endpoint to verify that the DNS Health Analyzer API is running."""
    return {
        "app": "DNS Health Analyzer API",
        "status": "online",
        "message": "Welcome to the DNS Health Analyzer API",
    }


@app.get("/health", summary="Service Health Check")
async def health_check():
    """Health check endpoint providing API and MongoDB connection status."""
    db_healthy = await db_manager.ping()
    return {
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
    }
