"""
Ground Stations API router.
Handles endpoints for retrieving ground station information.
"""
from fastapi import APIRouter
import structlog

from app.schemas.schemas import GroundStationsResponse, GroundStationResponse
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ground-stations", tags=["ground-stations"])


@router.get("", response_model=GroundStationsResponse)
async def get_ground_stations():
    """
    Get list of configured ground stations.
    
    Returns:
        List of ground stations with ID, name, coordinates, and minimum elevation
    """
    try:
        # Convert ground stations from config to response format
        ground_stations = [
            GroundStationResponse(
                id=gs['id'],
                name=gs['name'],
                lat=gs['lat'],
                lon=gs['lon'],
                min_elevation_deg=gs['min_elevation_deg']
            )
            for gs in settings.ground_stations
        ]
        
        logger.info("Ground stations retrieved", count=len(ground_stations))
        
        return GroundStationsResponse(ground_stations=ground_stations)
        
    except Exception as e:
        logger.error("Failed to retrieve ground stations", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve ground stations: {str(e)}"
        )
