from fastapi import FastAPI

app = FastAPI(
    title="DNS Health Analyzer API",
    description="Backend service for DNS Health diagnostics and monitoring",
    version="1.0.0",
)


@app.get("/")
def root():
    """Root endpoint to verify that the DNS Health Analyzer API is running."""
    return {
        "app": "DNS Health Analyzer API",
        "status": "online",
        "message": "Welcome to the DNS Health Analyzer API",
    }


@app.get("/health")
def health_check():
    """Health check endpoint to verify service operational status."""
    return {
        "status": "healthy",
    }
