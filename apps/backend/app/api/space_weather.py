"""
Space Weather API router.
Handles endpoints for retrieving space weather data from NASA DONKI.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query
import structlog

from app.schemas.schemas import SpaceWeatherResponse, SpaceWeatherEvent
from app.services.space_weather_client import space_weather_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/space-weather", tags=["space-weather"])


def build_event_description(event: dict) -> str:
    """Build human-readable description for a space weather event."""
    event_type = event.get('event_type', '')
    severity = event.get('severity', 'unknown')
    
    if event_type == 'FLR':
        class_type = event.get('class_type', '')
        return f"Solar Flare ({class_type}) - {severity} intensity"
    elif event_type == 'GST':
        kp_index = event.get('kp_index', 'N/A')
        return f"Geomagnetic Storm (Kp={kp_index}) - {severity}"
    elif event_type == 'CME':
        speed = event.get('speed', 'N/A')
        return f"Coronal Mass Ejection (Speed: {speed} km/s) - {severity}"
    else:
        return f"Space weather event ({event_type}) - {severity}"


@router.get("", response_model=SpaceWeatherResponse)
async def get_space_weather(
    start: Optional[str] = Query(None, description="Start time in ISO 8601 UTC format"),
    end: Optional[str] = Query(None, description="End time in ISO 8601 UTC format")
):
    """
    Get space weather events from NASA DONKI API.
    
    Returns solar flares, geomagnetic storms, and coronal mass ejections
    that may affect satellite communication link quality.
    
    Query Parameters:
        start: Start time (default: 24 hours ago)
        end: End time (default: 48 hours from now)
    
    Returns:
        Space weather events with overall status and communication impact assessment
    """
    try:
        # Parse time range
        if start:
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_time = datetime.utcnow() - timedelta(hours=24)
        
        if end:
            end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
        else:
            end_time = datetime.utcnow() + timedelta(hours=48)
        
        # Fetch space weather events
        space_weather = await space_weather_client.get_space_weather_events(
            start_time,
            end_time
        )
        
        # Assess communication impact
        communication_impact = space_weather_client.is_communication_affected(space_weather)
        
        # Convert events to response format
        events = []
        for event_type, event_list in space_weather.get('events', {}).items():
            for event in event_list:
                events.append(SpaceWeatherEvent(
                    event_type=event.get('event_type', event_type),
                    start_time=event.get('start_time', ''),
                    end_time=event.get('end_time'),
                    severity=event.get('severity', 'unknown'),
                    description=build_event_description(event)
                ))
        
        logger.info(
            "Space weather data retrieved",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            event_count=len(events),
            overall_status=space_weather.get('overall_status')
        )
        
        return SpaceWeatherResponse(
            events=events,
            overall_status=space_weather.get('overall_status', 'unknown'),
            communication_impact=communication_impact
        )
        
    except Exception as e:
        logger.error(
            "Failed to retrieve space weather data",
            error=str(e)
        )
        # Return empty response on error
        return SpaceWeatherResponse(
            events=[],
            overall_status='unknown',
            communication_impact={
                'affected': False,
                'overall_status': 'unknown',
                'risk_factors': [],
                'recommendation': 'Unable to fetch space weather data'
            }
        )
