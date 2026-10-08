"""DNS Health Analyzer FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.api.analysis import router as analysis_router
from app.database.mongodb import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dns_analyzer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle events."""
    # Startup: connect to MongoDB
    logger.info("Initializing application and connecting to MongoDB...")
    connected = await db_manager.connect()
    if connected:
        logger.info("Successfully connected to MongoDB.")
    else:
        logger.warning(
            "MongoDB not connected on startup. Live endpoints requiring database will return 503 until connection is established."
        )

    yield

    # Shutdown: close MongoDB client
    logger.info("Shutting down application and closing database connections...")
    await db_manager.close()


app = FastAPI(
    title="DNS Health Analyzer API",
    description="Backend service for DNS health diagnostics, record verification, and monitoring.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API routes
app.include_router(analysis_router)


@app.get("/")
def root():
    """Root endpoint to verify that the DNS Health Analyzer API is running."""
    return {
        "app": "DNS Health Analyzer API",
        "status": "online",
        "message": "Welcome to the DNS Health Analyzer API",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint providing API and MongoDB connection status."""
    db_healthy = await db_manager.ping()
    return {
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
    }
