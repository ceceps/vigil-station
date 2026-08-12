"""
Weather data client using Open-Meteo API.
Fetches weather conditions for ground stations to inform scheduling decisions.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
import httpx

logger = structlog.get_logger(__name__)


class WeatherClient:
    """Client for fetching weather data from Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    async def get_weather_for_ground_station(
        self,
        lat: float,
        lon: float,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Fetch weather forecast for a ground station location.
        
        Args:
            lat: Latitude of the ground station
            lon: Longitude of the ground station
            start_time: Start of the forecast period
            end_time: End of the forecast period
        
        Returns:
            Dictionary with weather data including cloud cover, precipitation, visibility
        """
        try:
            # Open-Meteo API parameters
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "hourly": "cloudcover,precipitation,visibility",
                "timezone": "UTC"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
            
            logger.info(
                "Weather data fetched",
                lat=lat,
                lon=lon,
                start=start_time.isoformat(),
                end=end_time.isoformat()
            )
            
            return self._parse_weather_data(data)
            
        except httpx.HTTPError as e:
            logger.error(
                "Failed to fetch weather data",
                lat=lat,
                lon=lon,
                error=str(e)
            )
            # Return empty data on error
            return {
                "hourly": {
                    "time": [],
                    "cloudcover": [],
                    "precipitation": [],
                    "visibility": []
                }
            }
        except Exception as e:
            logger.error(
                "Unexpected error fetching weather data",
                lat=lat,
                lon=lon,
                error=str(e)
            )
            return {
                "hourly": {
                    "time": [],
                    "cloudcover": [],
                    "precipitation": [],
                    "visibility": []
                }
            }
    
    def _parse_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Open-Meteo API response."""
        return {
            "hourly": raw_data.get("hourly", {}),
            "latitude": raw_data.get("latitude"),
            "longitude": raw_data.get("longitude"),
            "timezone": raw_data.get("timezone", "UTC")
        }
    
    async def get_weather_at_time(
        self,
        lat: float,
        lon: float,
        target_time: datetime
    ) -> Dict[str, Any]:
        """
        Get weather conditions at a specific time.
        
        Args:
            lat: Latitude
            lon: Longitude
            target_time: Specific time to get weather for
        
        Returns:
            Weather conditions at the target time
        """
        # Fetch weather for a 24-hour window around the target time
        start_time = target_time - timedelta(hours=12)
        end_time = target_time + timedelta(hours=12)
        
        weather_data = await self.get_weather_for_ground_station(
            lat, lon, start_time, end_time
        )
        
        # Find the closest time entry
        hourly = weather_data.get("hourly", {})
        times = hourly.get("time", [])
        
        if not times:
            return {
                "cloud_cover_percent": None,
                "precipitation_mm": None,
                "visibility_km": None,
                "conditions": "unknown"
            }
        
        # Find closest time index
        target_time_str = target_time.strftime("%Y-%m-%dT%H:00")
        closest_idx = 0
        min_diff = float('inf')
        
        target_time_naive = target_time.replace(tzinfo=None) if target_time.tzinfo else target_time
        for idx, time_str in enumerate(times):
            time_obj = datetime.fromisoformat(time_str)
            time_obj_naive = time_obj.replace(tzinfo=None) if time_obj.tzinfo else time_obj
            diff = abs((time_obj_naive - target_time_naive).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_idx = idx
        
        # Extract weather at closest time
        cloud_cover = hourly.get("cloudcover", [])[closest_idx] if closest_idx < len(hourly.get("cloudcover", [])) else None
        precipitation = hourly.get("precipitation", [])[closest_idx] if closest_idx < len(hourly.get("precipitation", [])) else None
        visibility = hourly.get("visibility", [])[closest_idx] if closest_idx < len(hourly.get("visibility", [])) else None
        
        # Determine conditions
        conditions = self._determine_conditions(cloud_cover, precipitation)
        
        return {
            "cloud_cover_percent": cloud_cover,
            "precipitation_mm": precipitation,
            "visibility_km": visibility / 1000 if visibility else None,  # Convert m to km
            "conditions": conditions,
            "timestamp": times[closest_idx]
        }
    
    def _determine_conditions(
        self,
        cloud_cover: Optional[float],
        precipitation: Optional[float]
    ) -> str:
        """Determine weather conditions from cloud cover and precipitation."""
        if cloud_cover is None:
            return "unknown"
        
        if precipitation and precipitation > 0.5:
            return "rainy"
        elif cloud_cover > 80:
            return "overcast"
        elif cloud_cover > 50:
            return "cloudy"
        elif cloud_cover > 20:
            return "partly_cloudy"
        else:
            return "clear"
    
    def is_weather_favorable(self, weather: Dict[str, Any]) -> bool:
        """
        Determine if weather conditions are favorable for satellite communication.
        
        Args:
            weather: Weather data dictionary
        
        Returns:
            True if conditions are favorable, False otherwise
        """
        cloud_cover = weather.get("cloud_cover_percent")
        precipitation = weather.get("precipitation_mm")
        conditions = weather.get("conditions")
        
        # Unfavorable conditions
        if conditions in ["rainy", "overcast"]:
            return False
        
        if precipitation and precipitation > 1.0:
            return False
        
        if cloud_cover and cloud_cover > 85:
            return False
        
        return True


# Global client instance
weather_client = WeatherClient()
