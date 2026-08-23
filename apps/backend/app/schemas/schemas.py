"""
Pydantic schemas for API request/response validation.
Defines the exact JSON structure for all API endpoints.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Satellite schemas
class SatelliteResponse(BaseModel):
    """Response schema for a single satellite."""
    norad_id: int = Field(..., description="NORAD catalog ID")
    name: str = Field(..., description="Satellite name")
    group: str = Field(..., description="Satellite group (e.g., 'iridium')")


class SatellitesResponse(BaseModel):
    """Response schema for list of satellites."""
    satellites: List[SatelliteResponse]


# Ground station schemas
class GroundStationResponse(BaseModel):
    """Response schema for a single ground station."""
    id: int = Field(..., description="Ground station ID")
    name: str = Field(..., description="Ground station name")
    lat: float = Field(..., description="Latitude in degrees")
    lon: float = Field(..., description="Longitude in degrees")
    min_elevation_deg: float = Field(..., description="Minimum elevation angle in degrees")


class GroundStationsResponse(BaseModel):
    """Response schema for list of ground stations."""
    ground_stations: List[GroundStationResponse]


# Pass window schemas
class PassWindowResponse(BaseModel):
    """Response schema for a single pass window."""
    id: str = Field(..., description="Unique pass ID")
    satellite_id: int = Field(..., description="NORAD catalog ID of the satellite")
    ground_station_id: int = Field(..., description="Ground station ID")
    start_time: str = Field(..., description="Pass start time in ISO 8601 UTC format")
    end_time: str = Field(..., description="Pass end time in ISO 8601 UTC format")
    max_elevation_deg: float = Field(..., description="Maximum elevation angle during the pass")


class PassesResponse(BaseModel):
    """Response schema for list of pass windows."""
    passes: List[PassWindowResponse]


# Conflict schemas
class ConflictResponse(BaseModel):
    """Response schema for a scheduling conflict."""
    id: str = Field(..., description="Unique identifier for the conflict")
    ground_station_id: int = Field(..., description="Ground station ID where conflict occurs")
    pass_ids: List[str] = Field(..., description="List of conflicting pass IDs")
    overlap_start: str = Field(..., description="Start of overlap in ISO 8601 UTC format")
    overlap_end: str = Field(..., description="End of overlap in ISO 8601 UTC format")


class ConflictsResponse(BaseModel):
    """Response schema for list of conflicts."""
    conflicts: List[ConflictResponse]


# Recommendation schemas
class AlternativeWindow(BaseModel):
    """Alternative time window for rescheduling."""
    start_time: str = Field(..., description="Alternative start time in ISO 8601 UTC format")
    end_time: str = Field(..., description="Alternative end time in ISO 8601 UTC format")


class RecommendationResponse(BaseModel):
    """Response schema for an AI-generated recommendation."""
    conflict_id: str = Field(..., description="ID of the conflict being addressed")
    suggested_action: str = Field(..., description="Suggested action (e.g., 'reschedule', 'prioritize')")
    target_pass_id: Optional[str] = Field(None, description="Pass ID to be rescheduled")
    alternative_window: Optional[AlternativeWindow] = Field(None, description="Alternative time window")
    reasoning: str = Field(..., description="Natural language explanation of the recommendation")


class RecommendationRequest(BaseModel):
    """Request schema for generating a recommendation."""
    conflict_id: str = Field(..., description="ID of the conflict to resolve")


class RecommendationResponseWrapper(BaseModel):
    """Wrapper for recommendation response."""
    recommendation: RecommendationResponse


# Schedule approval schemas
class ScheduleApprovalRequest(BaseModel):
    """Request schema for approving/overriding a schedule."""
    approved: bool = Field(..., description="Whether the schedule is approved")
    override_reason: Optional[str] = Field(None, description="Reason for override if not approved")


class ScheduleApprovalResponse(BaseModel):
    """Response schema for schedule approval."""
    status: str = Field(..., description="Status of the approval (e.g., 'approved', 'overridden')")
    schedule_id: str = Field(..., description="ID of the schedule that was approved/overridden")


# Weather data schemas (for P1)
class WeatherData(BaseModel):
    """Weather data for a ground station."""
    ground_station_id: int
    timestamp: str
    cloud_cover_percent: Optional[float] = None
    precipitation_mm: Optional[float] = None
    visibility_km: Optional[float] = None
    conditions: Optional[str] = None


# Space weather data schemas (for P1)
class SpaceWeatherEvent(BaseModel):
    """Space weather event data."""
    event_type: str = Field(..., description="Type of event (e.g., 'solar_flare', 'geomagnetic_storm')")
    start_time: str = Field(..., description="Event start time in ISO 8601 UTC format")
    end_time: Optional[str] = Field(None, description="Event end time in ISO 8601 UTC format")
    severity: str = Field(..., description="Event severity (e.g., 'minor', 'moderate', 'severe')")
    description: str = Field(..., description="Event description")


class SpaceWeatherCommunicationImpact(BaseModel):
    """Assessment of space weather impact on communication."""
    affected: bool = Field(..., description="Whether communication may be affected")
    overall_status: str = Field(..., description="Overall space weather status")
    risk_factors: List[str] = Field(default_factory=list, description="List of risk factors")
    recommendation: str = Field(..., description="Recommendation for operators")


class SpaceWeatherResponse(BaseModel):
    """Response schema for space weather data."""
    events: List[SpaceWeatherEvent] = Field(default_factory=list, description="List of space weather events")
    overall_status: str = Field(..., description="Overall space weather status")
    communication_impact: SpaceWeatherCommunicationImpact = Field(..., description="Communication impact assessment")
    data_available: bool = Field(default=True, description="Whether data was successfully fetched from NASA")
