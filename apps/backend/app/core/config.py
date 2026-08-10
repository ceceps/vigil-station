"""
Configuration management for the Mission Planning Assistant.
Loads settings from environment variables using pydantic-settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Space-Track.org credentials
    spacetrack_username: str = Field(..., description="Space-Track.org username")
    spacetrack_password: str = Field(..., description="Space-Track.org password")
    
    # Anthropic Claude API
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")
    
    # NASA DONKI API (optional for P1)
    nasa_api_key: str = Field(default="DEMO_KEY", description="NASA API key")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./mission_planning.db",
        description="Database connection URL"
    )
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=True, description="Debug mode")
    
    # CORS origins
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Cache settings
    tle_cache_hours: int = Field(
        default=6,
        description="Hours to cache TLE data before refetching"
    )
    
    # Satellite group to track
    satellite_group: str = Field(
        default="iridium",
        description="Satellite group to fetch from Space-Track"
    )
    
    # Ground stations (hardcoded for demo)
    ground_stations: List[dict] = Field(
        default=[
            {
                "id": 1,
                "name": "Jakarta Ground Station",
                "lat": -6.2088,
                "lon": 106.8456,
                "min_elevation_deg": 10
            },
            {
                "id": 2,
                "name": "Singapore Ground Station",
                "lat": 1.3521,
                "lon": 103.8198,
                "min_elevation_deg": 10
            },
            {
                "id": 3,
                "name": "Bandung Ground Station",
                "lat": -6.9175,
                "lon": 107.6191,
                "min_elevation_deg": 10
            }
        ],
        description="Ground station configurations"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
