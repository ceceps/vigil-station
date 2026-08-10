"""
Satellites API router.
Handles endpoints for retrieving satellite information.
"""
from typing import List
from fastapi import APIRouter, HTTPException
import structlog

from app.schemas.schemas import SatellitesResponse, SatelliteResponse
from app.services.spacetrack_client import spacetrack_service
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/satellites", tags=["satellites"])


@router.get("", response_model=SatellitesResponse)
async def get_satellites():
    """
    Get list of tracked satellites.
    
    Returns:
        List of satellites with NORAD ID, name, and group
    """
    try:
        # Fetch TLEs from cache or Space-Track
        tles = await spacetrack_service.fetch_tles_for_group(
            settings.satellite_group
        )
        
        # Convert to response format
        satellites = [
            SatelliteResponse(
                norad_id=tle['norad_id'],
                name=tle['name'],
                group=tle.get('group', settings.satellite_group)
            )
            for tle in tles
        ]
        
        # Sort by NORAD ID
        satellites.sort(key=lambda s: s.norad_id)
        
        logger.info("Satellites retrieved", count=len(satellites))
        
        return SatellitesResponse(satellites=satellites)
        
    except Exception as e:
        logger.error("Failed to retrieve satellites", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch satellites: {str(e)}"
        )
