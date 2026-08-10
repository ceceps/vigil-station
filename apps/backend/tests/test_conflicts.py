"""
Unit tests for conflicts API endpoint.
Tests the conflict detection functionality.
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
def mock_overlapping_passes():
    """Mock overlapping pass data for testing."""
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
        }
    ]


@pytest.fixture
def mock_non_overlapping_passes():
    """Mock non-overlapping pass data for testing."""
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
            'id': 'pass_24793_1_20260810100000',
            'satellite_id': 24793,
            'ground_station_id': 1,
            'start_time': (base_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'end_time': (base_time + timedelta(hours=1, minutes=10)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
            'max_elevation_deg': 38.2
        }
    ]


class TestConflictsEndpoint:
    """Test suite for conflicts API endpoint."""
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_with_overlaps(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_overlapping_passes):
        """Test conflict detection with overlapping passes."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_overlapping_passes
        
        response = client.get(
            "/conflicts",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'conflicts' in data
        assert len(data['conflicts']) > 0
        
        # Verify conflict structure
        conflict = data['conflicts'][0]
        assert 'id' in conflict
        assert 'ground_station_id' in conflict
        assert 'pass_ids' in conflict
        assert 'overlap_start' in conflict
        assert 'overlap_end' in conflict
        assert len(conflict['pass_ids']) == 2
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_no_overlaps(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_non_overlapping_passes):
        """Test conflict detection with no overlapping passes."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_non_overlapping_passes
        
        response = client.get(
            "/conflicts",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'conflicts' in data
        assert len(data['conflicts']) == 0
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_with_ground_station_filter(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_overlapping_passes):
        """Test conflict detection filtered by ground station."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_overlapping_passes
        
        response = client.get(
            "/conflicts",
            params={
                'ground_station_id': 1,
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(c['ground_station_id'] == 1 for c in data['conflicts'])
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_default_time_window(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_overlapping_passes):
        """Test conflict detection with default time window."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_overlapping_passes
        
        response = client.get("/conflicts")
        
        assert response.status_code == 200
        data = response.json()
        assert 'conflicts' in data
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_ground_station_not_found(self, mock_orbit_calc, mock_spacetrack, client, mock_tles):
        """Test conflict detection with non-existent ground station."""
        mock_spacetrack.return_value = mock_tles
        
        response = client.get(
            "/conflicts",
            params={
                'ground_station_id': 99999,
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_conflicts_spacetrack_failure(self, mock_spacetrack, client):
        """Test handling of Space-Track API failure."""
        mock_spacetrack.side_effect = Exception("Space-Track API unavailable")
        
        response = client.get(
            "/conflicts",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 500
        assert 'Failed to detect conflicts' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_datetime_format(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_overlapping_passes):
        """Test that datetime fields are properly formatted."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_overlapping_passes
        
        response = client.get(
            "/conflicts",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for conflict in data['conflicts']:
            # Verify datetime format (ISO 8601 with Z suffix)
            assert conflict['overlap_start'].endswith('Z')
            assert conflict['overlap_end'].endswith('Z')
            
            # Verify can be parsed
            start = datetime.fromisoformat(conflict['overlap_start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(conflict['overlap_end'].replace('Z', '+00:00'))
            assert start < end
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_id_format(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_overlapping_passes):
        """Test that conflict IDs follow expected format."""
        mock_spacetrack.return_value = mock_tles
        mock_orbit_calc.return_value = mock_overlapping_passes
        
        response = client.get(
            "/conflicts",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for conflict in data['conflicts']:
            # Conflict ID should start with "conflict_"
            assert conflict['id'].startswith('conflict_')
            # Should contain both pass IDs
            for pass_id in conflict['pass_ids']:
                assert pass_id in conflict['id']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_get_conflicts_multiple_stations(self, mock_orbit_calc, mock_spacetrack, client, mock_tles, mock_overlapping_passes):
        """Test conflict detection across multiple ground stations."""
        mock_spacetrack.return_value = mock_tles
        
        # Create passes for multiple stations
        station1_passes = mock_overlapping_passes
        station2_passes = [
            {**p, 'ground_station_id': 2, 'id': p['id'].replace('_1_', '_2_')}
            for p in mock_overlapping_passes
        ]
        
        def mock_calc(tles, gs, start, end):
            if gs['id'] == 1:
                return station1_passes
            elif gs['id'] == 2:
                return station2_passes
            return []
        
        mock_orbit_calc.side_effect = mock_calc
        
        response = client.get(
            "/conflicts",
            params={
                'start': '2026-08-10T00:00:00Z',
                'end': '2026-08-11T00:00:00Z'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have conflicts from multiple stations
        station_ids = set(c['ground_station_id'] for c in data['conflicts'])
        assert len(station_ids) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
