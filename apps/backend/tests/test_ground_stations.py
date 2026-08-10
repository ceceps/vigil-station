"""
Unit tests for ground stations API endpoint.
Tests the ground station listing functionality.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestGroundStationsEndpoint:
    """Test suite for ground stations API endpoint."""
    
    def test_get_ground_stations_success(self, client):
        """Test successful retrieval of ground station list."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        assert 'ground_stations' in data
        assert len(data['ground_stations']) == 3
        
        # Verify first ground station structure
        gs = data['ground_stations'][0]
        assert 'id' in gs
        assert 'name' in gs
        assert 'lat' in gs
        assert 'lon' in gs
        assert 'min_elevation_deg' in gs
    
    def test_get_ground_stations_jakarta(self, client):
        """Test Jakarta ground station data."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find Jakarta station
        jakarta = next(
            (gs for gs in data['ground_stations'] if gs['name'] == 'Jakarta Ground Station'),
            None
        )
        
        assert jakarta is not None
        assert jakarta['id'] == 1
        assert jakarta['lat'] == -6.2088
        assert jakarta['lon'] == 106.8456
        assert jakarta['min_elevation_deg'] == 10.0
    
    def test_get_ground_stations_singapore(self, client):
        """Test Singapore ground station data."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find Singapore station
        singapore = next(
            (gs for gs in data['ground_stations'] if gs['name'] == 'Singapore Ground Station'),
            None
        )
        
        assert singapore is not None
        assert singapore['id'] == 2
        assert singapore['lat'] == 1.3521
        assert singapore['lon'] == 103.8198
        assert singapore['min_elevation_deg'] == 10.0
    
    def test_get_ground_stations_bandung(self, client):
        """Test Bandung ground station data."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find Bandung station
        bandung = next(
            (gs for gs in data['ground_stations'] if gs['name'] == 'Bandung Ground Station'),
            None
        )
        
        assert bandung is not None
        assert bandung['id'] == 3
        assert bandung['lat'] == -6.9175
        assert bandung['lon'] == 107.6191
        assert bandung['min_elevation_deg'] == 10.0
    
    def test_get_ground_stations_data_structure(self, client):
        """Test that response has correct data structure."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert 'ground_stations' in data
        assert isinstance(data['ground_stations'], list)
        
        # Verify each ground station has required fields
        for gs in data['ground_stations']:
            assert 'id' in gs
            assert 'name' in gs
            assert 'lat' in gs
            assert 'lon' in gs
            assert 'min_elevation_deg' in gs
            assert isinstance(gs['id'], int)
            assert isinstance(gs['name'], str)
            assert isinstance(gs['lat'], (int, float))
            assert isinstance(gs['lon'], (int, float))
            assert isinstance(gs['min_elevation_deg'], (int, float))
    
    def test_get_ground_stations_coordinates_valid(self, client):
        """Test that all ground station coordinates are valid."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        for gs in data['ground_stations']:
            # Latitude must be between -90 and 90
            assert -90 <= gs['lat'] <= 90
            # Longitude must be between -180 and 180
            assert -180 <= gs['lon'] <= 180
            # Min elevation must be positive
            assert gs['min_elevation_deg'] > 0
    
    def test_get_ground_stations_unique_ids(self, client):
        """Test that all ground station IDs are unique."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        ids = [gs['id'] for gs in data['ground_stations']]
        assert len(ids) == len(set(ids))  # All IDs are unique
    
    def test_get_ground_stations_sorted_by_id(self, client):
        """Test that ground stations are sorted by ID."""
        response = client.get("/ground-stations")
        
        assert response.status_code == 200
        data = response.json()
        
        ids = [gs['id'] for gs in data['ground_stations']]
        assert ids == sorted(ids)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
