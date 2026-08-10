"""
End-to-End (E2E) tests for the complete mission planning workflow.
Tests the full flow: satellites → passes → conflicts → recommendations → approval.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tle_data():
    """Mock TLE data for testing."""
    return [
        {
            'norad_id': 24792,
            'name': 'IRIDIUM 8',
            'tle_line1': '1 24792U 97020B   26221.50000000  .00000000  00000-0  00000-0 0  9999',
            'tle_line2': '2 24792  86.4000   0.0000 0002000   0.0000  90.0000 14.34000000000000',
            'satellite_group': 'iridium',
            'group': 'iridium'
        },
        {
            'norad_id': 24793,
            'name': 'IRIDIUM 9',
            'tle_line1': '1 24793U 97020C   26221.50000000  .00000000  00000-0  00000-0 0  9999',
            'tle_line2': '2 24793  86.4000   0.0000 0002000   0.0000  90.0000 14.34000000000000',
            'satellite_group': 'iridium',
            'group': 'iridium'
        }
    ]


@pytest.fixture
def mock_passes():
    """Mock pass data that will create conflicts."""
    now = datetime.utcnow()
    return [
        {
            'id': 'pass_24792_1_test',
            'satellite_id': 24792,
            'ground_station_id': 1,
            'start_time': now + timedelta(hours=2),
            'end_time': now + timedelta(hours=2, minutes=12),
            'max_elevation_deg': 45.0
        },
        {
            'id': 'pass_24793_1_test',
            'satellite_id': 24793,
            'ground_station_id': 1,
            'start_time': now + timedelta(hours=2, minutes=5),  # Overlaps with first pass
            'end_time': now + timedelta(hours=2, minutes=17),
            'max_elevation_deg': 38.0
        }
    ]


class TestE2EWorkflow:
    """End-to-end workflow tests."""
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_complete_workflow_with_conflict_resolution(
        self,
        mock_store_schedule,
        mock_llm,
        mock_calc_passes,
        mock_fetch_tles,
        client,
        mock_tle_data,
        mock_passes
    ):
        """
        Test the complete workflow from satellite fetch to schedule approval.
        
        Workflow:
        1. Fetch satellites
        2. Calculate passes
        3. Detect conflicts
        4. Generate recommendation
        5. Approve schedule
        """
        # Setup mocks
        mock_fetch_tles.return_value = mock_tle_data
        mock_calc_passes.return_value = mock_passes
        mock_store_schedule.return_value = None
        
        # Mock LLM recommendation - will be set dynamically based on actual conflict_id
        def mock_llm_response(conflict, alternatives, weather):
            return {
                'conflict_id': conflict['id'],
                'suggested_action': 'reschedule',
                'target_pass_id': 'pass_24793_1_test',
                'alternative_window': {
                    'start_time': (datetime.utcnow() + timedelta(hours=4)).isoformat() + 'Z',
                    'end_time': (datetime.utcnow() + timedelta(hours=4, minutes=12)).isoformat() + 'Z'
                },
                'reasoning': 'The alternative pass maintains good elevation and avoids conflict.'
            }
        mock_llm.side_effect = mock_llm_response
        
        # Step 1: Fetch satellites
        response = client.get("/satellites")
        assert response.status_code == 200
        satellites = response.json()['satellites']
        assert len(satellites) == 2
        assert satellites[0]['norad_id'] == 24792
        
        # Step 2: Calculate passes for both satellites
        start_time = datetime.utcnow().isoformat() + 'Z'
        end_time = (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
        
        response = client.get(
            f"/passes?ground_station_id=1&start={start_time}&end={end_time}"
        )
        assert response.status_code == 200
        passes = response.json()['passes']
        assert len(passes) == 2
        
        # Step 3: Detect conflicts
        response = client.get(
            f"/conflicts?ground_station_id=1&start={start_time}&end={end_time}"
        )
        assert response.status_code == 200
        conflicts = response.json()['conflicts']
        assert len(conflicts) > 0
        
        conflict = conflicts[0]
        assert conflict['ground_station_id'] == 1
        assert len(conflict['pass_ids']) == 2
        
        # Step 4: Generate recommendation for the conflict
        response = client.post(
            "/recommendations",
            json={'conflict_id': conflict['id']}
        )
        assert response.status_code == 200
        recommendation = response.json()['recommendation']
        
        assert recommendation['conflict_id'] == conflict['id']
        assert recommendation['suggested_action'] == 'reschedule'
        assert 'reasoning' in recommendation
        assert len(recommendation['reasoning']) > 0
        
        # Step 5: Approve the recommended schedule
        target_pass_id = recommendation['target_pass_id']
        response = client.post(
            f"/schedule/{target_pass_id}/approve",
            json={
                'approved': True,
                'override_reason': None
            }
        )
        assert response.status_code == 200
        approval = response.json()
        
        assert approval['status'] == 'approved'
        assert approval['schedule_id'] == target_pass_id
        
        # Verify store_schedule was called
        assert mock_store_schedule.called
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    @patch('app.api.schedule.tle_cache.store_schedule')
    def test_workflow_with_override(
        self,
        mock_store_schedule,
        mock_llm,
        mock_calc_passes,
        mock_fetch_tles,
        client,
        mock_tle_data,
        mock_passes
    ):
        """
        Test workflow where operator overrides AI recommendation.
        """
        # Setup mocks
        mock_fetch_tles.return_value = mock_tle_data
        mock_calc_passes.return_value = mock_passes
        mock_store_schedule.return_value = None
        
        def mock_llm_response_override(conflict, alternatives, weather):
            return {
                'conflict_id': conflict['id'],
                'suggested_action': 'reschedule',
                'target_pass_id': 'pass_24793_1_test',
                'alternative_window': {
                    'start_time': (datetime.utcnow() + timedelta(hours=4)).isoformat() + 'Z',
                    'end_time': (datetime.utcnow() + timedelta(hours=4, minutes=12)).isoformat() + 'Z'
                },
                'reasoning': 'Alternative pass suggested.'
            }
        mock_llm.side_effect = mock_llm_response_override
        
        # Get conflicts
        start_time = datetime.utcnow().isoformat() + 'Z'
        end_time = (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
        
        response = client.get(
            f"/conflicts?ground_station_id=1&start={start_time}&end={end_time}"
        )
        conflicts = response.json()['conflicts']
        
        # Get recommendation
        response = client.post(
            "/recommendations",
            json={'conflict_id': conflicts[0]['id']}
        )
        recommendation = response.json()['recommendation']
        
        # Override the recommendation
        response = client.post(
            f"/schedule/{recommendation['target_pass_id']}/approve",
            json={
                'approved': False,
                'override_reason': 'Operator prefers original schedule due to mission priority'
            }
        )
        
        assert response.status_code == 200
        approval = response.json()
        assert approval['status'] == 'rejected'
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    def test_workflow_no_conflicts(
        self,
        mock_calc_passes,
        mock_fetch_tles,
        client,
        mock_tle_data
    ):
        """
        Test workflow when there are no scheduling conflicts.
        """
        # Setup mocks with non-overlapping passes
        now = datetime.utcnow()
        non_overlapping_passes = [
            {
                'id': 'pass_24792_1_test',
                'satellite_id': 24792,
                'ground_station_id': 1,
                'start_time': now + timedelta(hours=2),
                'end_time': now + timedelta(hours=2, minutes=12),
                'max_elevation_deg': 45.0
            },
            {
                'id': 'pass_24793_1_test',
                'satellite_id': 24793,
                'ground_station_id': 1,
                'start_time': now + timedelta(hours=4),  # No overlap
                'end_time': now + timedelta(hours=4, minutes=12),
                'max_elevation_deg': 38.0
            }
        ]
        
        mock_fetch_tles.return_value = mock_tle_data
        mock_calc_passes.return_value = non_overlapping_passes
        
        # Get satellites
        response = client.get("/satellites")
        assert response.status_code == 200
        
        # Get passes
        start_time = datetime.utcnow().isoformat() + 'Z'
        end_time = (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
        
        response = client.get(
            f"/passes?ground_station_id=1&start={start_time}&end={end_time}"
        )
        assert response.status_code == 200
        passes = response.json()['passes']
        assert len(passes) == 2
        
        # Check for conflicts - should be none
        response = client.get(
            f"/conflicts?ground_station_id=1&start={start_time}&end={end_time}"
        )
        assert response.status_code == 200
        conflicts = response.json()['conflicts']
        assert len(conflicts) == 0
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    def test_workflow_spacetrack_failure(
        self,
        mock_fetch_tles,
        client
    ):
        """
        Test workflow handles Space-Track API failures gracefully.
        """
        # Mock Space-Track failure
        mock_fetch_tles.side_effect = Exception("Space-Track API unavailable")
        
        # Attempt to fetch satellites
        response = client.get("/satellites")
        assert response.status_code == 500
        assert 'Failed to fetch satellites' in response.json()['detail']
    
    @patch('app.services.spacetrack_client.spacetrack_service.fetch_tles_for_group')
    @patch('app.services.orbit_calc.orbit_calculator.calculate_passes_for_multiple_satellites')
    @patch('app.services.llm_reasoner.llm_reasoner.generate_recommendation')
    def test_workflow_llm_failure(
        self,
        mock_llm,
        mock_calc_passes,
        mock_fetch_tles,
        client,
        mock_tle_data,
        mock_passes
    ):
        """
        Test workflow handles LLM failures gracefully.
        """
        # Setup mocks
        mock_fetch_tles.return_value = mock_tle_data
        mock_calc_passes.return_value = mock_passes
        mock_llm.side_effect = Exception("LLM service unavailable")
        
        # Get conflicts
        start_time = datetime.utcnow().isoformat() + 'Z'
        end_time = (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
        
        response = client.get(
            f"/conflicts?ground_station_id=1&start={start_time}&end={end_time}"
        )
        conflicts = response.json()['conflicts']
        
        # Attempt to get recommendation - should fail gracefully
        response = client.post(
            "/recommendations",
            json={'conflict_id': conflicts[0]['id']}
        )
        assert response.status_code == 500
        assert 'Failed to generate recommendation' in response.json()['detail']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
