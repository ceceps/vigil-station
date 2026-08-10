"""
Passes API router.
Handles endpoints for calculating and retrieving satellite pass windows.
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
import structlog

from app.schemas.schemas import PassesResponse, PassWindowResponse
from app.services.spacetrack_client import spacetrack_service
from app.services.orbit_calc import orbit_calculator
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/passes", tags=["passes"])


def serialize_datetime(dt) -> str:
    """Serialize datetime to ISO 8601 string with Z suffix."""
    if isinstance(dt, datetime):
        # Ensure UTC and format with Z
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=None)
        return dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    elif isinstance(dt, str):
        # Already a string, ensure it has Z suffix
        if not dt.endswith('Z'):
            return dt.rstrip('+00:00') + 'Z'
        return dt
    return str(dt)


@router.get("", response_model=PassesResponse)
async def get_passes(
    satellite_id: Optional[int] = Query(None, description="NORAD catalog ID of satellite"),
    ground_station_id: Optional[int] = Query(None, description="Ground station ID"),
    start: Optional[str] = Query(None, description="Start time in ISO 8601 UTC format"),
    end: Optional[str] = Query(None, description="End time in ISO 8601 UTC format")
):
    """
    Calculate pass windows for satellites over ground stations.
    
    Query Parameters:
        - satellite_id: Optional filter for specific satellite
        - ground_station_id: Optional filter for specific ground station
        - start: Start of time window (defaults to now)
        - end: End of time window (defaults to 24 hours from start)
    
    Returns:
        List of pass windows with timing and elevation data
    """
    try:
        # Parse time parameters
        if start:
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_time = datetime.utcnow()
        
        if end:
            end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
        else:
            end_time = start_time + timedelta(hours=24)
        
        logger.info(
            "Calculating passes",
            satellite_id=satellite_id,
            ground_station_id=ground_station_id,
            start=start_time.isoformat(),
            end=end_time.isoformat()
        )
        
        # Fetch TLE data
        tles = await spacetrack_service.fetch_tles_for_group(settings.satellite_group)
        
        # Filter by satellite_id if specified
        if satellite_id:
            tles = [tle for tle in tles if tle['norad_id'] == satellite_id]
            if not tles:
                raise HTTPException(
                    status_code=404,
                    detail=f"Satellite with NORAD ID {satellite_id} not found"
                )
        
        # Get ground stations
        ground_stations = settings.ground_stations
        
        # Filter by ground_station_id if specified
        if ground_station_id:
            ground_stations = [gs for gs in ground_stations if gs['id'] == ground_station_id]
            if not ground_stations:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ground station with ID {ground_station_id} not found"
                )
        
        # Calculate passes for all combinations
        all_passes = []
        seen_pass_ids = set()
        
        for gs in ground_stations:
            passes = orbit_calculator.calculate_passes_for_multiple_satellites(
                tles,
                gs,
                start_time,
                end_time
            )
            # Deduplicate passes by ID
            for p in passes:
                if p['id'] not in seen_pass_ids:
                    all_passes.append(p)
                    seen_pass_ids.add(p['id'])
        
        # Convert to response format with proper datetime serialization
        pass_responses = [
            PassWindowResponse(
                id=p['id'],
                satellite_id=p['satellite_id'],
                ground_station_id=p['ground_station_id'],
                start_time=serialize_datetime(p['start_time']),
                end_time=serialize_datetime(p['end_time']),
                max_elevation_deg=round(p['max_elevation_deg'], 2)
            )
            for p in all_passes
        ]
        
        logger.info("Passes calculated", count=len(pass_responses))
        
        return PassesResponse(passes=pass_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to calculate passes", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate passes: {str(e)}"
        )