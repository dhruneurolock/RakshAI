"""
RakshAI Backend
Main FastAPI application entry point
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app
import logging
import structlog

from app.core.config import settings
from app.core.database import engine, Base, ensure_sqlite_schema
from app.api.v1 import api_router
from app.core.websocket_manager import websocket_manager


def configure_runtime_logging() -> None:
    """Ensure backend logs are emitted to both terminal and backend.log for live diagnostics."""
    log_level = getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and str(getattr(handler, "baseFilename", "")).endswith("backend.log")
        for handler in root_logger.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler("backend.log", encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    has_stream_handler = any(
        type(handler) is logging.StreamHandler
        for handler in root_logger.handlers
    )
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)


configure_runtime_logging()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated Web Application Penetration Testing with Deterministic Rule-Based Attack Planning",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting RakshAI backend", environment=settings.ENVIRONMENT)
    # Create database tables
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    logger.info("Database tables created")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RakshAI backend")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RakshAI API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(client_id, websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            logger.info("WebSocket message received", client_id=client_id, data=data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info("WebSocket disconnected", client_id=client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
