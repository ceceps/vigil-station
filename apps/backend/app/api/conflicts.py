"""
Conflicts API router.
Handles endpoints for detecting and retrieving scheduling conflicts.
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
import structlog

from app.schemas.schemas import ConflictsResponse, ConflictResponse
from app.services.spacetrack_client import spacetrack_service
from app.services.orbit_calc import orbit_calculator
from app.services.conflict_detector import conflict_detector
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


@router.get("", response_model=ConflictsResponse)
async def get_conflicts(
    ground_station_id: Optional[int] = Query(None, description="Ground station ID to check for conflicts"),
    start: Optional[str] = Query(None, description="Start time in ISO 8601 UTC format"),
    end: Optional[str] = Query(None, description="End time in ISO 8601 UTC format")
):
    """
    Detect scheduling conflicts at ground stations.
    
    A conflict occurs when two or more satellite passes overlap in time
    at the same ground station.
    
    Query Parameters:
        - ground_station_id: Optional filter for specific ground station
        - start: Start of time window (defaults to now)
        - end: End of time window (defaults to 24 hours from start)
    
    Returns:
        List of conflicts with overlapping pass information
    """
    try:
        # Parse time parameters
        if start:
            start_time = datetime.fromisoformat(start.replace('Z', ''))
        else:
            start_time = datetime.utcnow()
        
        if end:
            end_time = datetime.fromisoformat(end.replace('Z', ''))
        else:
            end_time = start_time + timedelta(hours=24)
        
        logger.info(
            "Detecting conflicts",
            ground_station_id=ground_station_id,
            start=start_time.isoformat(),
            end=end_time.isoformat()
        )
        
        # Fetch TLE data
        tles = await spacetrack_service.fetch_tles_for_group(settings.satellite_group)
        
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
        
        # Calculate passes for all ground stations
        passes_by_station = {}
        for gs in ground_stations:
            passes = orbit_calculator.calculate_passes_for_multiple_satellites(
                tles,
                gs,
                start_time,
                end_time
            )
            passes_by_station[gs['id']] = passes
        
        # Detect conflicts
        all_conflicts = conflict_detector.detect_conflicts_all_stations(passes_by_station)
        
        # Convert to response format (remove full pass data from response)
        conflict_responses = [
            ConflictResponse(
                id=c['id'],
                ground_station_id=c['ground_station_id'],
                pass_ids=c['pass_ids'],
                overlap_start=c['overlap_start'],
                overlap_end=c['overlap_end']
            )
            for c in all_conflicts
        ]
        
        logger.info("Conflicts detected", count=len(conflict_responses))
        
        return ConflictsResponse(conflicts=conflict_responses)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to detect conflicts", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect conflicts: {str(e)}"
        )
