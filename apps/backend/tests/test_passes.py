"""
Unit tests for passes API endpoint.
Tests the satellite pass window calculation functionality.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


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
            'start_time': base_time,
            'end_time': base_time + timedelta(minutes=10),
            'max_elevation_deg': 45.5
        },
        {
            'id': 'pass_24793_1_20260810100000',
            'satellite_id': 24793,
            'ground_station_id': 1,
            'start_time': base_time + timedelta(hours=1),
            'end_time': base_time + timedelta(hours=1, minutes=10),
            'max_elevation_deg': 38.2
        }
    ]


class TestPassesEndpoint:
    """Test suite for passes API endpoint."""
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_success(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_passes):
        """Test successful pass calculation."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        
        response = client.get(
            "/passes",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'passes' in data
        assert len(data['passes']) == 2
        
        # Verify pass structure
        pass_data = data['passes'][0]
        assert 'id' in pass_data
        assert 'satellite_id' in pass_data
        assert 'ground_station_id' in pass_data
        assert 'start_time' in pass_data
        assert 'end_time' in pass_data
        assert 'max_elevation_deg' in pass_data
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_with_satellite_filter(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_passes):
        """Test pass calculation filtered by satellite ID."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = [mock_passes[0]]  # Only first satellite
        
        response = client.get(
            "/passes",
            params={
                'satellite_id': 24792,
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['passes']) == 1
        assert data['passes'][0]['satellite_id'] == 24792
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_with_ground_station_filter(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_passes):
        """Test pass calculation filtered by ground station ID."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        
        response = client.get(
            "/passes",
            params={
                'ground_station_id': 1,
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(p['ground_station_id'] == 1 for p in data['passes'])
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_default_time_window(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_passes):
        """Test pass calculation with default time window (24 hours)."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        
        response = client.get("/passes")
        
        assert response.status_code == 200
        data = response.json()
        assert 'passes' in data
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_passes_satellite_not_found(self, mock_spacetrack, client, mock_tles):
        """Test pass calculation with non-existent satellite ID."""
        mock_spacetrack.return_value = mock_tles
        
        response = client.get(
            "/passes",
            params={
                'satellite_id': 99999,
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_ground_station_not_found(self, mock_orbit_calc, mock_spacetrack, client, mock_tles):
        """Test pass calculation with non-existent ground station ID."""
        mock_spacetrack.return_value = mock_tles
        
        response = client.get(
            "/passes",
            params={
                'ground_station_id': 99999,
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_empty_result(self, mock_orbit_calc, mock_spacetrack, client, mock_tles):
        """Test pass calculation with no passes found."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = []
        
        response = client.get(
            "/passes",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['passes']) == 0
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_passes_spacetrack_failure(self, mock_spacetrack, client):
        """Test handling of Space-Track API failure."""
        mock_spacetrack.side_effect = Exception("Space-Track API unavailable")
        
        response = client.get(
            "/passes",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 500
        assert 'Failed to calculate passes' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_datetime_format(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_passes):
        """Test that datetime fields are properly formatted."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        
        response = client.get(
            "/passes",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for pass_data in data['passes']:
            # Verify datetime format (ISO 8601 with Z suffix)
            assert pass_data['start_time'].endswith('Z')
            assert pass_data['end_time'].endswith('Z')
            
            # Verify can be parsed
            start = datetime.fromisoformat(pass_data['start_time'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(pass_data['end_time'].replace('Z', '+00:00'))
            assert start < end
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_passes_elevation_rounded(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_passes):
        """Test that elevation is rounded to 2 decimal places."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_passes
        
        response = client.get(
            "/passes",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for pass_data in data['passes']:
            elevation = pass_data['max_elevation_deg']
            # Check it's rounded to 2 decimal places
            assert elevation == round(elevation, 2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
