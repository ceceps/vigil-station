"""
Unit tests for schedule API endpoint.
Tests the schedule approval/override functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestScheduleEndpoint:
    """Test suite for schedule API endpoint."""
    
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_approve_schedule_success(self, mock_store_schedule, client):
        """Test successful schedule approval."""
        # Mock store_schedule to do nothing (success)
        mock_store_schedule.return_value = None
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'approved'
        assert data['schedule_id'] == 'pass_24792_1_20260810090000'
        
        # Verify store_schedule was called
        assert mock_store_schedule.called
    
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_override_schedule_success(self, mock_store_schedule, client):
        """Test successful schedule override."""
        # Mock store_schedule to do nothing (success)
        mock_store_schedule.return_value = None
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': False,
                'override_reason': 'Weather conditions unfavorable'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'rejected'
        assert data['schedule_id'] == 'pass_24792_1_20260810090000'
        
        # Verify store_schedule was called
        assert mock_store_schedule.called
    
    @patch('app.api.schedule.tle_cache.get_schedule')
    def test_approve_schedule_not_found(self, mock_get_schedule, client):
        """Test approval of non-existent schedule."""
        # Mock get_schedule to return None (not found)
        mock_get_schedule.return_value = None
        
        response = client.get("/schedule/nonexistent_id/status")
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()
    
    def test_approve_schedule_missing_approved_field(self, client):
        """Test approval with missing 'approved' field."""
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'override_reason': 'Some reason'
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_override_without_reason(self, client):
        """Test override without providing a reason."""
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': False,
                'override_reason': None
            }
        )
        
        # Should fail validation - override requires a reason
        assert response.status_code == 400
        assert 'reason' in response.json()['detail'].lower()
    
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_approve_already_approved_schedule(self, mock_store_schedule, client):
        """Test approval of already approved schedule."""
        # Mock store_schedule to do nothing (success)
        mock_store_schedule.return_value = None
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        
        # Should succeed - idempotent operation
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'approved'
    
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_database_error_handling(self, mock_store_schedule, client):
        """Test handling of database errors."""
        # Mock store_schedule to raise exception
        mock_store_schedule.side_effect = Exception("Database connection failed")
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        
        assert response.status_code == 500
        assert 'Failed to process approval' in response.json()['detail']
    
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_approve_with_optional_reason(self, mock_store_schedule, client):
        """Test approval with optional reason provided."""
        # Mock store_schedule to do nothing (success)
        mock_store_schedule.return_value = None
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': True,
                'override_reason': 'Operator confirmed optimal conditions'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'approved'
    
    @patch('app.api.schedule.tle_cache.get_schedule')
    def test_schedule_id_validation(self, mock_get_schedule, client):
        """Test that schedule ID format is validated."""
        # Mock get_schedule to return None (not found)
        mock_get_schedule.return_value = None
        
        # Test with various invalid IDs
        invalid_ids = [
            'invalid',
            '123',
            'pass_',
            '_1_20260810090000'
        ]
        
        for invalid_id in invalid_ids:
            response = client.get(f"/schedule/{invalid_id}/status")
            
            # Should return 404 (not found)
            assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])