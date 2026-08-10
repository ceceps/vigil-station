"""
Space weather data client using NASA DONKI API.
Fetches space weather events (solar flares, geomagnetic storms, CMEs) 
that may affect satellite communication link quality.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
import httpx

from app.core.config import settings

logger = structlog.get_logger(__name__)


class SpaceWeatherClient:
    """Client for fetching space weather data from NASA DONKI API."""
    
    BASE_URL = "https://api.nasa.gov/DONKI"
    
    # Event type mappings for DONKI API
    EVENT_TYPES = {
        "solar_flare": "FLR",
        "coronal_mass_ejection": "CME",
        "geomagnetic_storm": "GST",
        "interplanetary_shock": "IPS",
        "solar_energetic_particle": "SEP",
        "magnetopause_crossing": "MPC",
        "radiation_belt_enhancement": "RBE",
        "high_speed_stream": "HSS",
        "wave": "WAV"
    }
    
    # Severity mappings based on event class/scale
    SEVERITY_LEVELS = {
        "X": "extreme",
        "M": "strong",
        "C": "moderate",
        "G5": "extreme",
        "G4": "severe",
        "G3": "strong",
        "G2": "moderate",
        "G1": "minor"
    }
    
    async def get_space_weather_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch space weather events from NASA DONKI API.
        
        Args:
            start_time: Start of the query period
            end_time: End of the query period
            event_types: Optional list of event types to fetch
                        (e.g., ['solar_flare', 'geomagnetic_storm'])
        
        Returns:
            Dictionary with space weather events grouped by type
        """
        if event_types is None:
            event_types = ["solar_flare", "coronal_mass_ejection", "geomagnetic_storm"]
        
        all_events = {}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for event_type in event_types:
                donki_type = self.EVENT_TYPES.get(event_type)
                if not donki_type:
                    continue
                
                try:
                    events = await self._fetch_event_type(
                        client, donki_type, start_time, end_time
                    )
                    all_events[event_type] = events
                    
                except Exception as e:
                    logger.warning(
                        "Failed to fetch space weather events",
                        event_type=event_type,
                        error=str(e)
                    )
                    all_events[event_type] = []
        
        # Calculate overall space weather status
        overall_status = self._calculate_overall_status(all_events)
        
        logger.info(
            "Space weather events fetched",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            event_counts={k: len(v) for k, v in all_events.items()},
            overall_status=overall_status
        )
        
        return {
            "events": all_events,
            "overall_status": overall_status,
            "query_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }
    
    async def _fetch_event_type(
        self,
        client: httpx.AsyncClient,
        donki_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch a specific event type from DONKI API."""
        
        params = {
            "startDate": start_time.strftime("%Y-%m-%d"),
            "endDate": end_time.strftime("%Y-%m-%d"),
            "api_key": settings.nasa_api_key
        }
        
        url = f"{self.BASE_URL}/{donki_type}"
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        raw_events = response.json()
        return self._parse_events(raw_events, donki_type)
    
    def _parse_events(self, raw_events: List[Dict], event_type: str) -> List[Dict[str, Any]]:
        """Parse raw DONKI API events into standardized format."""
        
        parsed = []
        for event in raw_events:
            parsed_event = {
                "event_id": event.get("eventID", ""),
                "event_type": event_type,
                "start_time": event.get("startTime", ""),
                "end_time": event.get("endTime"),
                "source_location": event.get("sourceLocation", ""),
                "active": event.get("active", False),
                "instruments": event.get("instruments", []),
                "linked_events": event.get("linkedEvents", [])
            }
            
            # Add severity based on event type
            if event_type == "FLR":
                parsed_event["severity"] = self._get_flare_severity(event)
                parsed_event["class_type"] = event.get("classType", "")
            elif event_type == "GST":
                parsed_event["severity"] = self._get_storm_severity(event)
                parsed_event["kp_index"] = event.get("kpIndex")
            elif event_type == "CME":
                parsed_event["severity"] = self._get_cme_severity(event)
                parsed_event["speed"] = event.get("speed")
            else:
                parsed_event["severity"] = "unknown"
            
            parsed.append(parsed_event)
        
        return parsed
    
    def _get_flare_severity(self, event: Dict) -> str:
        """Determine solar flare severity from class type."""
        class_type = event.get("classType", "")
        if not class_type:
            return "unknown"
        
        # Extract the letter prefix (X, M, C, B, A)
        prefix = class_type[0].upper() if class_type else ""
        return self.SEVERITY_LEVELS.get(prefix, "minor")
    
    def _get_storm_severity(self, event: Dict) -> str:
        """Determine geomagnetic storm severity from Kp index."""
        kp = event.get("kpIndex")
        if kp is None:
            return "unknown"
        
        try:
            kp_val = int(kp) if isinstance(kp, str) else kp
            if kp_val >= 9:
                return "extreme"
            elif kp_val >= 7:
                return "severe"
            elif kp_val >= 5:
                return "strong"
            elif kp_val >= 3:
                return "moderate"
            else:
                return "minor"
        except (ValueError, TypeError):
            return "unknown"
    
    def _get_cme_severity(self, event: Dict) -> str:
        """Determine CME severity from speed."""
        speed = event.get("speed")
        if speed is None:
            return "unknown"
        
        try:
            speed_val = int(speed) if isinstance(speed, str) else speed
            if speed_val >= 2000:
                return "extreme"
            elif speed_val >= 1000:
                return "severe"
            elif speed_val >= 500:
                return "strong"
            else:
                return "moderate"
        except (ValueError, TypeError):
            return "unknown"
    
    def _calculate_overall_status(self, events: Dict[str, List]) -> str:
        """Calculate overall space weather status from all events."""
        
        severity_priority = {
            "extreme": 4,
            "severe": 3,
            "strong": 2,
            "moderate": 1,
            "minor": 0,
            "unknown": 0
        }
        
        max_severity = 0
        active_events = []
        
        for event_type, event_list in events.items():
            for event in event_list:
                if event.get("active", False):
                    severity = event.get("severity", "unknown")
                    severity_val = severity_priority.get(severity, 0)
                    if severity_val > max_severity:
                        max_severity = severity_val
                    active_events.append(event)
        
        if max_severity >= 4:
            return "extreme"
        elif max_severity >= 3:
            return "severe"
        elif max_severity >= 2:
            return "disturbed"
        elif max_severity >= 1:
            return "unsettled"
        else:
            return "quiet"
    
    def is_communication_affected(self, space_weather: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess if space weather conditions may affect satellite communication.
        
        Args:
            space_weather: Space weather data dictionary
        
        Returns:
            Assessment of communication impact
        """
        overall_status = space_weather.get("overall_status", "quiet")
        events = space_weather.get("events", {})
        
        affected = False
        risk_factors = []
        
        # Check for active geomagnetic storms
        gst_events = events.get("geomagnetic_storm", [])
        for gst in gst_events:
            if gst.get("active", False):
                severity = gst.get("severity", "unknown")
                if severity in ["extreme", "severe", "strong"]:
                    affected = True
                    risk_factors.append(f"Active geomagnetic storm: {severity}")
        
        # Check for solar flares
        flare_events = events.get("solar_flare", [])
        for flare in flare_events:
            if flare.get("active", False):
                severity = flare.get("severity", "unknown")
                if severity in ["extreme", "severe"]:
                    affected = True
                    risk_factors.append(f"Active solar flare: {severity}")
        
        # Check for CMEs
        cme_events = events.get("coronal_mass_ejection", [])
        for cme in cme_events:
            if cme.get("active", False):
                severity = cme.get("severity", "unknown")
                if severity in ["extreme", "severe"]:
                    affected = True
                    risk_factors.append(f"Active CME: {severity}")
        
        return {
            "affected": affected,
            "overall_status": overall_status,
            "risk_factors": risk_factors,
            "recommendation": self._get_recommendation(overall_status, affected)
        }
    
    def _get_recommendation(self, status: str, affected: bool) -> str:
        """Get communication recommendation based on space weather status."""
        if affected:
            return "Consider rescheduling passes during severe space weather events. Link quality may be degraded."
        elif status == "disturbed":
            return "Space weather is unsettled. Monitor conditions and have contingency plans."
        elif status == "unsettled":
            return "Space weather is slightly elevated. Minor effects possible on high-latitude links."
        else:
            return "Space weather conditions are favorable for satellite communication."


# Global client instance
space_weather_client = SpaceWeatherClient()
