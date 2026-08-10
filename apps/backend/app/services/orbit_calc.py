"""
Orbital mechanics calculations using Skyfield.
Calculates pass windows (visibility periods) between satellites and ground stations.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import structlog
from skyfield.api import load, wgs84, EarthSatellite, utc
from skyfield.toposlib import GeographicPosition

from app.core.config import settings

logger = structlog.get_logger(__name__)


class OrbitCalculator:
    """Service for calculating satellite pass windows using Skyfield."""
    
    def __init__(self):
        """Initialize the orbit calculator with Skyfield timescale."""
        self.ts = load.timescale()
        logger.info("Orbit calculator initialized")
    
    def _ensure_skyfield_utc(self, dt: datetime) -> datetime:
        """Ensure datetime has Skyfield's UTC timezone."""
        if dt.tzinfo is None:
            # Naive datetime - assume UTC and add Skyfield's UTC
            return dt.replace(tzinfo=utc)
        elif dt.tzinfo != utc:
            # Has timezone but not Skyfield's UTC - convert to UTC first, then use Skyfield's UTC
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.replace(tzinfo=utc)
        # Already has Skyfield's UTC
        return dt
    
    def calculate_passes(
        self,
        tle_data: Dict[str, Any],
        ground_station: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        min_elevation_deg: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate pass windows for a satellite over a ground station.
        
        Args:
            tle_data: Dictionary with keys 'name', 'tle_line1', 'tle_line2', 'norad_id'
            ground_station: Dictionary with keys 'id', 'name', 'lat', 'lon', 'min_elevation_deg'
            start_time: Start of the time window to search
            end_time: End of the time window to search
            min_elevation_deg: Minimum elevation angle (overrides ground_station setting if provided)
        
        Returns:
            List of pass dictionaries with start_time, end_time, max_elevation_deg
        """
        try:
            # Ensure times have Skyfield's UTC timezone
            start_time = self._ensure_skyfield_utc(start_time)
            end_time = self._ensure_skyfield_utc(end_time)
            
            # Create satellite object from TLE
            satellite = EarthSatellite(
                tle_data['tle_line1'],
                tle_data['tle_line2'],
                tle_data['name'],
                self.ts
            )
            
            # Create ground station location
            location = wgs84.latlon(
                ground_station['lat'],
                ground_station['lon']
            )
            
            # Use provided min elevation or ground station default
            min_elev = min_elevation_deg if min_elevation_deg is not None else ground_station['min_elevation_deg']
            
            # Convert datetime to Skyfield time
            t0 = self.ts.from_datetime(start_time)
            t1 = self.ts.from_datetime(end_time)
            
            # Find passes
            t, events = satellite.find_events(
                location,
                t0,
                t1,
                altitude_degrees=min_elev
            )
            
            # Parse events into passes
            passes = []
            current_pass = {}
            
            for ti, event in zip(t, events):
                # Get UTC-aware datetime (convert Skyfield UTC to Python timezone.utc for consistency)
                event_time_skyfield = ti.utc_datetime()
                event_time = event_time_skyfield.replace(tzinfo=timezone.utc)
                
                if event == 0:  # Rise
                    current_pass = {
                        'start_time': event_time,
                        'satellite_id': tle_data['norad_id'],
                        'ground_station_id': ground_station['id']
                    }
                elif event == 1:  # Culmination (maximum elevation)
                    if current_pass:
                        # Calculate elevation at culmination
                        difference = satellite - location
                        topocentric = difference.at(ti)
                        alt, az, distance = topocentric.altaz()
                        current_pass['max_elevation_deg'] = alt.degrees
                        current_pass['culmination_time'] = event_time
                elif event == 2:  # Set
                    if current_pass:
                        current_pass['end_time'] = event_time
                        
                        # Generate pass ID
                        pass_id = self._generate_pass_id(
                            tle_data['norad_id'],
                            ground_station['id'],
                            current_pass['start_time']
                        )
                        current_pass['id'] = pass_id
                        
                        passes.append(current_pass)
                        current_pass = {}
            
            logger.info(
                "Calculated passes",
                satellite=tle_data['name'],
                ground_station=ground_station['name'],
                count=len(passes)
            )
            
            return passes
            
        except Exception as e:
            logger.error(
                "Failed to calculate passes",
                satellite=tle_data.get('name'),
                ground_station=ground_station.get('name'),
                error=str(e)
            )
            raise
    
    def calculate_passes_for_multiple_satellites(
        self,
        tles: List[Dict[str, Any]],
        ground_station: Dict[str, Any],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Calculate passes for multiple satellites over a single ground station.
        
        Args:
            tles: List of TLE dictionaries
            ground_station: Ground station dictionary
            start_time: Start of the time window
            end_time: End of the time window
        
        Returns:
            Combined list of all passes, sorted by start time
        """
        all_passes = []
        
        for tle in tles:
            try:
                passes = self.calculate_passes(
                    tle,
                    ground_station,
                    start_time,
                    end_time
                )
                all_passes.extend(passes)
            except Exception as e:
                logger.warning(
                    "Skipping satellite due to calculation error",
                    satellite=tle.get('name'),
                    error=str(e)
                )
                continue
        
        # Sort by start time
        all_passes.sort(key=lambda p: p['start_time'])
        
        return all_passes
    
    def calculate_passes_for_all_ground_stations(
        self,
        tles: List[Dict[str, Any]],
        ground_stations: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Calculate passes for multiple satellites over multiple ground stations.
        
        Args:
            tles: List of TLE dictionaries
            ground_stations: List of ground station dictionaries
            start_time: Start of the time window
            end_time: End of the time window
        
        Returns:
            Dictionary mapping ground_station_id to list of passes
        """
        passes_by_station = {}
        
        for gs in ground_stations:
            passes = self.calculate_passes_for_multiple_satellites(
                tles,
                gs,
                start_time,
                end_time
            )
            passes_by_station[gs['id']] = passes
        
        logger.info(
            "Calculated passes for all ground stations",
            ground_station_count=len(ground_stations),
            total_passes=sum(len(p) for p in passes_by_station.values())
        )
        
        return passes_by_station
    
    def get_satellite_position(
        self,
        tle_data: Dict[str, Any],
        time: datetime
    ) -> Dict[str, float]:
        """
        Get satellite position at a specific time.
        
        Args:
            tle_data: TLE dictionary
            time: Time to calculate position
        
        Returns:
            Dictionary with lat, lon, altitude_km
        """
        try:
            # Ensure time has Skyfield's UTC timezone
            time = self._ensure_skyfield_utc(time)
            
            satellite = EarthSatellite(
                tle_data['tle_line1'],
                tle_data['tle_line2'],
                tle_data['name'],
                self.ts
            )
            
            t = self.ts.from_datetime(time)
            geocentric = satellite.at(t)
            subpoint = wgs84.subpoint(geocentric)
            
            return {
                'lat': subpoint.latitude.degrees,
                'lon': subpoint.longitude.degrees,
                'altitude_km': subpoint.elevation.km
            }
            
        except Exception as e:
            logger.error(
                "Failed to calculate satellite position",
                satellite=tle_data.get('name'),
                error=str(e)
            )
            raise
    
    def _generate_pass_id(
        self,
        satellite_id: int,
        ground_station_id: int,
        start_time: datetime
    ) -> str:
        """Generate a unique pass ID."""
        timestamp = start_time.strftime('%Y%m%d%H%M%S')
        return f"pass_{satellite_id}_{ground_station_id}_{timestamp}"


# Global calculator instance
orbit_calculator = OrbitCalculator()
