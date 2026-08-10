"""
Space-Track.org client for fetching TLE data.
Handles authentication and TLE retrieval with proper rate limiting.
"""
from typing import List, Dict, Any, Optional
import structlog
from spacetrack import SpaceTrackClient

from app.core.config import settings
from app.core.cache import tle_cache

logger = structlog.get_logger(__name__)


class SpaceTrackService:
    """Service for interacting with Space-Track.org API."""
    
    def __init__(self):
        """Initialize the Space-Track client."""
        self.client: Optional[SpaceTrackClient] = None
        self._authenticated = False
    
    def _authenticate(self) -> None:
        """Authenticate with Space-Track.org."""
        if self._authenticated and self.client:
            return
        
        try:
            self.client = SpaceTrackClient(
                identity=settings.spacetrack_username,
                password=settings.spacetrack_password
            )
            self._authenticated = True
            logger.info("Successfully authenticated with Space-Track.org")
        except Exception as e:
            logger.error("Failed to authenticate with Space-Track.org", error=str(e))
            raise
    
    async def fetch_tles_for_group(
        self,
        satellite_group: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch TLE data for a satellite group.
        Uses cache if available and valid, otherwise fetches from Space-Track.
        
        Args:
            satellite_group: Name of the satellite group (e.g., 'iridium')
            force_refresh: Force fetch from Space-Track even if cache is valid
        
        Returns:
            List of TLE dictionaries with keys: norad_id, name, tle_line1, tle_line2
        """
        # Check cache first
        if not force_refresh and tle_cache.is_cache_valid(satellite_group):
            logger.info(
                "Using cached TLE data",
                satellite_group=satellite_group
            )
            return tle_cache.get_tles(satellite_group)
        
        # Fetch from Space-Track
        logger.info(
            "Fetching TLE data from Space-Track.org",
            satellite_group=satellite_group
        )
        
        self._authenticate()
        
        try:
            # Query Space-Track for the satellite group
            # Using the GP (General Perturbations) class which supports 6-digit catalog numbers
            if satellite_group.lower() == "iridium":
                # Fetch Iridium constellation
                # NORAD IDs for Iridium NEXT constellation (examples)
                # In production, you'd query by OBJECT_NAME like 'IRIDIUM%'
                gp_data = self.client.gp(
                    norad_cat_id=range(43569, 43580),  # Sample Iridium NEXT satellites
                    orderby='norad_cat_id',
                    limit=10,
                    format='3le'  # Three-line element format
                )
            else:
                # Generic query for other groups
                gp_data = self.client.gp(
                    object_name=f'{satellite_group.upper()}%',
                    orderby='norad_cat_id',
                    limit=10,
                    format='3le'
                )
            
            # Parse the 3LE format response
            tles = self._parse_3le_format(gp_data, satellite_group)
            
            # Store in cache
            if tles:
                tle_cache.store_tles(tles, satellite_group)
                logger.info(
                    "TLE data fetched and cached",
                    satellite_group=satellite_group,
                    count=len(tles)
                )
            else:
                logger.warning(
                    "No TLE data found for group",
                    satellite_group=satellite_group
                )
            
            return tles
            
        except Exception as e:
            logger.error(
                "Failed to fetch TLE data from Space-Track.org",
                satellite_group=satellite_group,
                error=str(e)
            )
            # Fall back to cache if available
            cached_tles = tle_cache.get_tles(satellite_group)
            if cached_tles:
                logger.warning(
                    "Using stale cached TLE data due to fetch failure",
                    satellite_group=satellite_group
                )
                return cached_tles
            raise
    
    def _parse_3le_format(self, gp_data: str, satellite_group: str) -> List[Dict[str, Any]]:
        """
        Parse 3LE (Three-Line Element) format from Space-Track.
        
        Format:
        Line 0: Satellite name
        Line 1: TLE line 1
        Line 2: TLE line 2
        
        Args:
            gp_data: Raw 3LE format string from Space-Track
            satellite_group: Satellite group name
        
        Returns:
            List of parsed TLE dictionaries
        """
        tles = []
        lines = gp_data.strip().split('\n')
        
        # Process in groups of 3 lines
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
            
            name = lines[i].strip()
            tle_line1 = lines[i + 1].strip()
            tle_line2 = lines[i + 2].strip()
            
            # Extract NORAD ID from TLE line 1 (columns 3-7)
            try:
                norad_id = int(tle_line1[2:7].strip())
            except (ValueError, IndexError):
                logger.warning(
                    "Failed to parse NORAD ID from TLE",
                    name=name,
                    tle_line1=tle_line1
                )
                continue
            
            tles.append({
                'norad_id': norad_id,
                'name': name,
                'tle_line1': tle_line1,
                'tle_line2': tle_line2,
                'satellite_group': satellite_group,
                'metadata': {}
            })
        
        return tles
    
    async def get_satellite_by_norad_id(self, norad_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific satellite's TLE by NORAD ID.
        
        Args:
            norad_id: NORAD catalog ID
        
        Returns:
            TLE dictionary or None if not found
        """
        # Check cache first
        tle = tle_cache.get_tle_by_norad_id(norad_id)
        if tle:
            return tle
        
        # If not in cache, try to fetch from Space-Track
        self._authenticate()
        
        try:
            gp_data = self.client.gp(
                norad_cat_id=norad_id,
                orderby='epoch desc',
                limit=1,
                format='3le'
            )
            
            tles = self._parse_3le_format(gp_data, 'unknown')
            if tles:
                # Store in cache
                tle_cache.store_tles(tles, 'unknown')
                return tles[0]
            
        except Exception as e:
            logger.error(
                "Failed to fetch TLE for NORAD ID",
                norad_id=norad_id,
                error=str(e)
            )
        
        return None


# Global service instance
spacetrack_service = SpaceTrackService()
