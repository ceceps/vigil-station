"""
Recommendations API router.
Handles endpoints for generating AI-powered conflict resolution recommendations.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
import structlog

from app.schemas.schemas import (
    RecommendationRequest,
    RecommendationResponseWrapper,
    RecommendationResponse
)
from app.services.spacetrack_client import spacetrack_service
from app.services.orbit_calc import orbit_calculator
from app.services.conflict_detector import conflict_detector
from app.services.llm_reasoner import llm_reasoner
from app.services.weather_client import weather_client
from app.services.space_weather_client import space_weather_client
from app.core.config import settings
from app.core.cache import tle_cache

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def serialize_datetime(dt) -> str:
    """Serialize datetime to ISO 8601 string with Z suffix."""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    elif isinstance(dt, str):
        if not dt.endswith('Z'):
            return dt.rstrip('+00:00') + 'Z'
        return dt
    return str(dt)


@router.post("", response_model=RecommendationResponseWrapper)
async def generate_recommendation(request: RecommendationRequest):
    """
    Generate an AI-powered recommendation for resolving a scheduling conflict.
    
    The recommendation includes:
    - Suggested action (reschedule, prioritize, defer)
    - Target pass to reschedule (if applicable)
    - Alternative time window (if available)
    - Natural language reasoning explaining the recommendation
    
    Request Body:
        - conflict_id: ID of the conflict to resolve
    
    Returns:
        Recommendation with suggested action and detailed reasoning
    """
    try:
        conflict_id = request.conflict_id
        
        logger.info("Generating recommendation", conflict_id=conflict_id)
        
        # Parse conflict_id to extract pass IDs
        # Format: conflict_pass_<id1>_pass_<id2>
        if not conflict_id.startswith("conflict_"):
            raise HTTPException(
                status_code=400,
                detail="Invalid conflict_id format"
            )
        
        # Extract pass IDs from conflict_id
        parts = conflict_id.replace("conflict_", "").split("_pass_")
        if len(parts) < 2:
            raise HTTPException(
                status_code=400,
                detail="Invalid conflict_id format"
            )
        
        pass1_id = "pass_" + parts[0].replace("pass_", "")
        pass2_id = "pass_" + parts[1]
        
        # Fetch TLE data and calculate passes to reconstruct the conflict
        tles = await spacetrack_service.fetch_tles_for_group(settings.satellite_group)
        
        # Use a 48-hour window to find the passes
        start_time = datetime.utcnow() - timedelta(hours=24)
        end_time = datetime.utcnow() + timedelta(hours=48)
        
        # Calculate passes for all ground stations
        passes_by_station = {}
        for gs in settings.ground_stations:
            passes = orbit_calculator.calculate_passes_for_multiple_satellites(
                tles,
                gs,
                start_time,
                end_time
            )
            passes_by_station[gs['id']] = passes
        
        # Find the specific passes involved in the conflict
        target_pass1 = None
        target_pass2 = None
        ground_station_id = None
        
        for gs_id, passes in passes_by_station.items():
            for p in passes:
                if p['id'] == pass1_id:
                    target_pass1 = p
                    ground_station_id = gs_id
                elif p['id'] == pass2_id:
                    target_pass2 = p
                    ground_station_id = gs_id
        
        if not target_pass1 or not target_pass2:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find passes for conflict {conflict_id}"
            )
        
        # Ensure datetime fields are properly formatted
        target_pass1['start_time'] = serialize_datetime(target_pass1['start_time'])
        target_pass1['end_time'] = serialize_datetime(target_pass1['end_time'])
        target_pass2['start_time'] = serialize_datetime(target_pass2['start_time'])
        target_pass2['end_time'] = serialize_datetime(target_pass2['end_time'])
        
        # Reconstruct the conflict
        overlap = conflict_detector._check_overlap(target_pass1, target_pass2)
        if not overlap:
            raise HTTPException(
                status_code=400,
                detail="Specified passes do not overlap"
            )
        
        overlap_start, overlap_end = overlap
        
        conflict = {
            'id': conflict_id,
            'ground_station_id': ground_station_id,
            'pass_ids': [pass1_id, pass2_id],
            'overlap_start': serialize_datetime(overlap_start),
            'overlap_end': serialize_datetime(overlap_end),
            'passes': [target_pass1, target_pass2]
        }
        
        # Find alternative windows for the second pass
        all_passes_for_station = passes_by_station[ground_station_id]
        
        # Serialize all pass times in the station list
        for p in all_passes_for_station:
            p['start_time'] = serialize_datetime(p['start_time'])
            p['end_time'] = serialize_datetime(p['end_time'])
        
        alternative_passes = conflict_detector.find_alternative_windows(
            target_pass2,
            all_passes_for_station,
            time_window_hours=48
        )
        
        # Serialize alternative pass times
        for alt in alternative_passes:
            alt['start_time'] = serialize_datetime(alt['start_time'])
            alt['end_time'] = serialize_datetime(alt['end_time'])
        
        # Get weather data for the ground station (P1 feature)
        weather_data = None
        try:
            ground_station = next(
                gs for gs in settings.ground_stations 
                if gs['id'] == ground_station_id
            )
            
            # Get weather at the time of the original pass
            pass_time = target_pass2['start_time']
            if isinstance(pass_time, str):
                pass_time = datetime.fromisoformat(pass_time.replace('Z', '+00:00'))
            
            weather = await weather_client.get_weather_at_time(
                ground_station['lat'],
                ground_station['lon'],
                pass_time
            )
            
            weather_data = {
                **weather,
                'is_favorable': weather_client.is_weather_favorable(weather)
            }
            
        except Exception as e:
            logger.warning(
                "Failed to fetch weather data for recommendation",
                error=str(e)
            )
        
        # Get space weather data (P1 feature)
        space_weather_data = None
        try:
            # Fetch space weather events for the time window
            start_time_dt = datetime.utcnow() - timedelta(hours=24)
            end_time_dt = datetime.utcnow() + timedelta(hours=48)
            
            space_weather = await space_weather_client.get_space_weather_events(
                start_time_dt,
                end_time_dt
            )
            
            # Assess communication impact
            communication_impact = space_weather_client.is_communication_affected(space_weather)
            
            space_weather_data = {
                **space_weather,
                'communication_impact': communication_impact
            }
            
        except Exception as e:
            logger.warning(
                "Failed to fetch space weather data for recommendation",
                error=str(e)
            )
        
        # Generate recommendation using LLM
        recommendation = await llm_reasoner.generate_recommendation(
            conflict,
            alternative_passes,
            weather_data,
            space_weather_data
        )
        
        # Persist recommendation in database
        try:
            tle_cache.store_recommendation(recommendation)
        except Exception as err:
            logger.warning("Failed to persist recommendation to database", error=str(err))

        logger.info(
            "Recommendation generated successfully",
            conflict_id=conflict_id,
            suggested_action=recommendation['suggested_action']
        )
        
        return RecommendationResponseWrapper(
            recommendation=RecommendationResponse(**recommendation)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to generate recommendation",
            conflict_id=request.conflict_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendation: {str(e)}"
        )