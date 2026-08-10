"""
Unit tests for recommendations API endpoint.
Tests the AI-powered conflict resolution recommendation generation.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.schemas import RecommendationRequest


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tles():
    """Mock TLE data for testing."""
    return [
        {
            'norad_id': 24792,
            'name': 'IRIDIUM 8',
            'line1': '1 24792U 97020B   26222.50000000  .00000000  00000-0  00000-0 0  9999',
            'line2': '2 24792  86.4000   0.0000 0002000   0.0000   0.0000 14.34000000000000'
        },
        {
            'norad_id': 24793,
            'name': 'IRIDIUM 7',
            'line1': '1 24793U 97020C   26222.50000000  .00000000  00000-0  00000-0 0  9999',
            'line2': '2 24793  86.4000   0.0000 0002000   0.0000   0.0000 14.34000000000000'
        }
    ]


@pytest.fixture
def mock_passes():
    """Mock pass data for testing."""
    base_time = datetime(2026, 8, 10, 9, 0, 0, tzinfo=timezone.utc)
    
    return [
        {
            'id': 'pass_24792_1_20260810090000',
            'satellite_id': 24792,
            'ground_station_id': 1,
            'start_time': base_time.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'end_time': (base_time + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'max_elevation_deg': 45.5
        },
        {
            'id': 'pass_24793_1_20260810090500',
            'satellite_id': 24793,
            'ground_station_id': 1,
            'start_time': (base_time + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'end_time': (base_time + timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'max_elevation_deg': 38.2
        },
        {
            'id': 'pass_24793_1_20260810100000',
            'satellite_id': 24793,
            'ground_station_id': 1,
            'start_time': (base_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'end_time': (base_time + timedelta(hours=1, minutes=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'max_elevation_deg': 42.0
        }
    ]


@pytest.fixture
def mock_weather():
    """Mock weather data for testing."""
    return {
        'temperature': 28.5,
        'cloud_cover': 20,
        'precipitation': 0.0,
        'wind_speed': 5.2,
        'is_favorable': True
    }


@pytest.fixture
def mock_recommendation():
    """Mock AI recommendation response."""
    return {
        'conflict_id': 'conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500',
        'suggested_action': 'reschedule',
        'target_pass_id': 'pass_24793_1_20260810090500',
        'alternative_window': {
            'start_time': '2026-08-10T10:00:00Z',
            'end_time': '2026-08-10T10:10:00Z'
        },
        'reasoning': 'Pass 1 (IRIDIUM 8) has higher elevation (45.5°) compared to Pass 2 (IRIDIUM 7, 38.2°). Recommend rescheduling Pass 2 to the alternative window at 10:00 UTC, which has no conflicts and maintains good elevation (42.0°). Weather conditions are favorable with 20% cloud cover.'
    }


class TestRecommendationsEndpoint:
    """Test suite for recommendations API endpoint."""
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.weather_client.weather_client.get_weather_at_time')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    def test_generate_recommendation_success(
        self,
        mock_llm,
        mock_weather_client,
        mock_orbit_calc,
        mock_spacetrack,
        client,
        mock_tles,
        mock_passes,
        mock_weather,
        mock_recommendation
    ):
        """Test successful recommendation generation."""
        # Setup mocks
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        mock_weather_client.return_value = mock_weather
        mock_llm.return_value = mock_recommendation
        
        # Make request
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert 'recommendation' in data
        assert data['recommendation']['suggested_action'] == 'reschedule'
        assert data['recommendation']['target_pass_id'] == 'pass_24793_1_20260810090500'
        assert 'reasoning' in data['recommendation']
        assert len(data['recommendation']['reasoning']) > 0
    
    def test_generate_recommendation_invalid_conflict_id(self, client):
        """Test recommendation generation with invalid conflict ID format."""
        response = client.post(
            "/recommendations",
            json={"conflict_id": "invalid_format"}
        )
        
        assert response.status_code == 400
        assert 'Invalid conflict_id format' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_generate_recommendation_passes_not_found(
        self,
        mock_orbit_calc,
        mock_spacetrack,
        client,
        mock_tles
    ):
        """Test recommendation generation when passes are not found."""
        # Setup mocks - return empty passes
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = []
        
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        assert response.status_code == 404
        assert 'Could not find passes' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_generate_recommendation_no_overlap(
        self,
        mock_orbit_calc,
        mock_spacetrack,
        client,
        mock_tles
    ):
        """Test recommendation generation when passes don't actually overlap."""
        # Setup mocks with non-overlapping passes
        base_time = datetime(2026, 8, 10, 9, 0, 0, tzinfo=timezone.utc)
        non_overlapping_passes = [
            {
                'id': 'pass_24792_1_20260810090000',
                'satellite_id': 24792,
                'ground_station_id': 1,
                'start_time': base_time.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                'end_time': (base_time + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                'max_elevation_deg': 45.5
            },
            {
                'id': 'pass_24793_1_20260810090500',
                'satellite_id': 24793,
                'ground_station_id': 1,
                'start_time': (base_time + timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                'end_time': (base_time + timedelta(minutes=25)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                'max_elevation_deg': 38.2
            }
        ]
        
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = non_overlapping_passes
        
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        assert response.status_code == 400
        assert 'do not overlap' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.weather_client.weather_client.get_weather_at_time')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    def test_generate_recommendation_with_weather_failure(
        self,
        mock_llm,
        mock_weather_client,
        mock_orbit_calc,
        mock_spacetrack,
        client,
        mock_tles,
        mock_passes,
        mock_recommendation
    ):
        """Test recommendation generation when weather API fails (should still succeed)."""
        # Setup mocks - weather fails but recommendation should still work
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        mock_weather_client.side_effect = Exception("Weather API unavailable")
        mock_llm.return_value = mock_recommendation
        
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        # Should still succeed even without weather data
        assert response.status_code == 200
        data = response.json()
        assert 'recommendation' in data
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_generate_recommendation_spacetrack_failure(
        self,
        mock_spacetrack,
        client
    ):
        """Test recommendation generation when Space-Track API fails."""
        mock_spacetrack.side_effect = Exception("Space-Track API unavailable")
        
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        assert response.status_code == 500
        assert 'Failed to generate recommendation' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    def test_generate_recommendation_llm_failure(
        self,
        mock_llm,
        mock_orbit_calc,
        mock_spacetrack,
        client,
        mock_tles,
        mock_passes
    ):
        """Test recommendation generation when LLM API fails."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        mock_llm.side_effect = Exception("LLM API unavailable")
        
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        assert response.status_code == 500
        assert 'Failed to generate recommendation' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.weather_client.weather_client.get_weather_at_time')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    def test_generate_recommendation_with_alternative_window(
        self,
        mock_llm,
        mock_weather_client,
        mock_orbit_calc,
        mock_spacetrack,
        client,
        mock_tles,
        mock_passes,
        mock_weather
    ):
        """Test recommendation includes alternative window when available."""
        # Setup recommendation with alternative window
        recommendation_with_alt = {
            'conflict_id': 'conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500',
            'suggested_action': 'reschedule',
            'target_pass_id': 'pass_24793_1_20260810090500',
            'alternative_window': {
                'start_time': '2026-08-10T10:00:00Z',
                'end_time': '2026-08-10T10:10:00Z'
            },
            'reasoning': 'Alternative window found at 10:00 UTC with no conflicts.'
        }
        
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        mock_weather_client.return_value = mock_weather
        mock_llm.return_value = recommendation_with_alt
        
        response = client.post(
            "/recommendations",
            json={"conflict_id": "conflict_pass_24792_1_20260810090000_pass_24793_1_20260810090500"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'alternative_window' in data['recommendation']
        assert data['recommendation']['alternative_window']['start_time'] == '2026-08-10T10:00:00Z'
    
    def test_generate_recommendation_missing_conflict_id(self, client):
        """Test recommendation generation with missing conflict_id."""
        response = client.post(
            "/recommendations",
            json={}
        )
        
        assert response.status_code == 422  # Validation error


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
