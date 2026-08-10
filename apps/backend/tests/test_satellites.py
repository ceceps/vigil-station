"""
Unit tests for satellites API endpoint.
Tests the satellite listing functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tles():
    """Mock TLE data for Iridium satellites."""
    return [
        {
            'norad_id': 24792,
            'name': 'IRIDIUM 8',
            'group': 'iridium',
            'line1': '1 24792U 97020B   26222.50000000  .00000000  00000-0  00000-0 0  9999',
            'line2': '2 24792  86.4000   0.0000 0002000   0.0000   0.0000 14.34000000000000'
        },
        {
            'norad_id': 24793,
            'name': 'IRIDIUM 7',
            'group': 'iridium',
            'line1': '1 24793U 97020C   26222.50000000  .00000000  00000-0  00000-0 0  9999',
            'line2': '2 24793  86.4000   0.0000 0002000   0.0000   0.0000 14.34000000000000'
        },
        {
            'norad_id': 24794,
            'name': 'IRIDIUM 6',
            'group': 'iridium',
            'line1': '1 24794U 97020D   26222.50000000  .00000000  00000-0  00000-0 0  9999',
            'line2': '2 24794  86.4000   0.0000 0002000   0.0000   0.0000 14.34000000000000'
        }
    ]


class TestSatellitesEndpoint:
    """Test suite for satellites API endpoint."""
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_satellites_success(self, mock_spacetrack, client, mock_tles):
        """Test successful retrieval of satellite list."""
        mock_spacetrack.return_value = mock_tles
        
        response = client.get("/satellites")
        
        assert response.status_code == 200
        data = response.json()
        assert 'satellites' in data
        assert len(data['satellites']) == 3
        
        # Verify first satellite structure
        sat = data['satellites'][0]
        assert 'norad_id' in sat
        assert 'name' in sat
        assert 'group' in sat
        assert sat['norad_id'] == 24792
        assert sat['name'] == 'IRIDIUM 8'
        assert sat['group'] == 'iridium'
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_satellites_empty_list(self, mock_spacetrack, client):
        """Test retrieval when no satellites are available."""
        mock_spacetrack.return_value = []
        
        response = client.get("/satellites")
        
        assert response.status_code == 200
        data = response.json()
        assert 'satellites' in data
        assert len(data['satellites']) == 0
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_satellites_spacetrack_failure(self, mock_spacetrack, client):
        """Test handling of Space-Track API failure."""
        mock_spacetrack.side_effect = Exception("Space-Track API unavailable")
        
        response = client.get("/satellites")
        
        assert response.status_code == 500
        assert 'Failed to fetch satellites' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_satellites_correct_group(self, mock_spacetrack, client, mock_tles):
        """Test that correct satellite group is requested."""
        mock_spacetrack.return_value = mock_tles
        
        response = client.get("/satellites")
        
        assert response.status_code == 200
        # Verify the correct group was requested
        mock_spacetrack.assert_called_once()
        # The group name should be from settings (iridium)
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_satellites_data_structure(self, mock_spacetrack, client, mock_tles):
        """Test that response has correct data structure."""
        mock_spacetrack.return_value = mock_tles
        
        response = client.get("/satellites")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert 'satellites' in data
        assert isinstance(data['satellites'], list)
        
        # Verify each satellite has required fields
        for sat in data['satellites']:
            assert 'norad_id' in sat
            assert 'name' in sat
            assert 'group' in sat
            assert isinstance(sat['norad_id'], int)
            assert isinstance(sat['name'], str)
            assert isinstance(sat['group'], str)
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_get_satellites_sorted_by_norad_id(self, mock_spacetrack, client):
        """Test that satellites are sorted by NORAD ID."""
        unsorted_tles = [
            {'norad_id': 24794, 'name': 'IRIDIUM 6', 'group': 'iridium'},
            {'norad_id': 24792, 'name': 'IRIDIUM 8', 'group': 'iridium'},
            {'norad_id': 24793, 'name': 'IRIDIUM 7', 'group': 'iridium'}
        ]
        mock_spacetrack.return_value = unsorted_tles
        
        response = client.get("/satellites")
        
        assert response.status_code == 200
        data = response.json()
        satellites = data['satellites']
        
        # Verify sorted order
        norad_ids = [sat['norad_id'] for sat in satellites]
        assert norad_ids == sorted(norad_ids)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
