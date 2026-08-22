"""
Mission Planning Assistant - FastAPI Backend
Main application entry point with router registration and middleware setup.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.models.database import init_db
from app.api import satellites, ground_stations, passes, conflicts, recommendations, schedule, space_weather, analytics
from app.services.spacetrack_client import spacetrack_service

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup logic
    logger.info(
        "Mission Planning Assistant starting",
        database="postgresql",
        satellite_group=settings.satellite_group,
        ground_stations=len(settings.ground_stations)
    )
    
    # Initialize database tables
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    # Pre-fetch TLE data on startup to populate cache
    try:
        await spacetrack_service.fetch_tles_for_group(settings.satellite_group)
        logger.info("TLE cache initialized on startup")
    except Exception as e:
        logger.warning(
            "Failed to initialize TLE cache on startup",
            error=str(e)
        )
    
    yield
    
    # Shutdown logic
    logger.info("Mission Planning Assistant shutting down")


# Create FastAPI application
app = FastAPI(
    title="Mission Planning Assistant API",
    description="Ground Station Contact Scheduling with AI Decision-Support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(satellites.router)
app.include_router(ground_stations.router)
app.include_router(passes.router)
app.include_router(conflicts.router)
app.include_router(recommendations.router)
app.include_router(schedule.router)
app.include_router(space_weather.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "name": "Mission Planning Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "postgresql",
        "satellite_group": settings.satellite_group,
        "ground_stations": len(settings.ground_stations)
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )