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


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session


class TestScheduleEndpoint:
    """Test suite for schedule API endpoint."""
    
    @patch('app.models.database.SessionLocal')
    def test_approve_schedule_success(self, mock_session_local, client):
        """Test successful schedule approval."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_schedule = MagicMock()
        mock_schedule.id = 'pass_24792_1_20260810090000'
        mock_schedule.status = 'pending'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_schedule
        
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
    
    @patch('app.models.database.SessionLocal')
    def test_override_schedule_success(self, mock_session_local, client):
        """Test successful schedule override."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_schedule = MagicMock()
        mock_schedule.id = 'pass_24792_1_20260810090000'
        mock_schedule.status = 'pending'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_schedule
        
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
    
    @patch('app.models.database.SessionLocal')
    def test_approve_schedule_not_found(self, mock_session_local, client):
        """Test approval of non-existent schedule."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.post(
            "/schedule/nonexistent_id/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        
        assert response.status_code == 404
        assert 'not found' in response.json()['detail']
    
    @patch('app.models.database.SessionLocal')
    def test_approve_schedule_missing_approved_field(self, mock_session_local, client):
        """Test approval with missing 'approved' field."""
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'override_reason': 'Some reason'
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.models.database.SessionLocal')
    def test_override_without_reason(self, mock_session_local, client):
        """Test override without providing a reason."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_schedule = MagicMock()
        mock_schedule.id = 'pass_24792_1_20260810090000'
        mock_schedule.status = 'pending'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_schedule
        
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
    
    @patch('app.models.database.SessionLocal')
    def test_approve_already_approved_schedule(self, mock_session_local, client):
        """Test approval of already approved schedule."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_schedule = MagicMock()
        mock_schedule.id = 'pass_24792_1_20260810090000'
        mock_schedule.status = 'approved'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_schedule
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        
        # Should succeed but indicate already approved
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'approved'
    
    @patch('app.models.database.SessionLocal')
    def test_database_error_handling(self, mock_session_local, client):
        """Test handling of database errors."""
        # Setup mock to raise exception
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("Database connection failed")
        
        response = client.post(
            "/schedule/pass_24792_1_20260810090000/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        
        assert response.status_code == 500
        assert 'Failed to update schedule' in response.json()['detail']
    
    @patch('app.models.database.SessionLocal')
    def test_approve_with_optional_reason(self, mock_session_local, client):
        """Test approval with optional reason provided."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_schedule = MagicMock()
        mock_schedule.id = 'pass_24792_1_20260810090000'
        mock_schedule.status = 'pending'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_schedule
        
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
    
    @patch('app.models.database.SessionLocal')
    def test_schedule_id_validation(self, mock_session_local, client):
        """Test that schedule ID format is validated."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Test with various invalid IDs
        invalid_ids = [
            '',
            'invalid',
            '123',
            'pass_',
            '_1_20260810090000'
        ]
        
        for invalid_id in invalid_ids:
            response = client.post(
                f"/schedule/{invalid_id}/approve",
                json={
                    'approved': True,
                    'override_reason': None
                }
            )
            
            # Should return 404 (not found) or 400 (bad request)
            assert response.status_code in [400, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
