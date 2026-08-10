# Backend Tests

This directory contains unit tests for the Mission Planning Assistant backend.

## Test Coverage

### Recommendations Endpoint (`test_recommendations.py`)

Comprehensive test suite for the AI-powered conflict resolution recommendation endpoint.

**Test Cases:**

1. ✅ **test_generate_recommendation_success** - Happy path with valid conflict
2. ✅ **test_generate_recommendation_invalid_conflict_id** - Invalid conflict ID format
3. ✅ **test_generate_recommendation_passes_not_found** - Passes not found in database
4. ✅ **test_generate_recommendation_no_overlap** - Passes don't actually overlap
5. ✅ **test_generate_recommendation_with_weather_failure** - Weather API fails (graceful degradation)
6. ✅ **test_generate_recommendation_spacetrack_failure** - Space-Track API fails
7. ✅ **test_generate_recommendation_llm_failure** - LLM API fails
8. ✅ **test_generate_recommendation_with_alternative_window** - Alternative window included
9. ✅ **test_generate_recommendation_missing_conflict_id** - Missing required field

## Running Tests

### Quick Start

```bash
cd apps/backend
./run_tests.sh
```

### Manual Execution

```bash
# Activate virtual environment
cd apps/backend
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_recommendations.py -v

# Run specific test
pytest tests/test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_success -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
```

## Test Structure

```
tests/
├── README.md                    # This file
├── test_recommendations.py      # Recommendations endpoint tests
├── __init__.py                  # Test package marker
└── conftest.py                  # Shared fixtures (optional)
```

## Fixtures

The test suite uses the following fixtures:

- **client** - FastAPI TestClient for making HTTP requests
- **mock_tles** - Mock TLE data for Iridium satellites
- **mock_passes** - Mock pass window data with overlapping times
- **mock_weather** - Mock weather data from Open-Meteo
- **mock_recommendation** - Mock AI recommendation response

## Mocking Strategy

Tests use `unittest.mock.patch` to mock external dependencies:

- `spacetrack_service.fetch_tles_for_group` - Space-Track.org API
- `orbit_calculator.calculate_passes_for_multiple_satellites` - Skyfield calculations
- `weather_client.get_weather_at_time` - Open-Meteo API
- `llm_reasoner.generate_recommendation` - Anthropic Claude API

This ensures tests run quickly and don't depend on external services.

## Test Results

Last run: 2026-08-10

```
========== test session starts ==========
collected 9 items

test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_success PASSED [ 11%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_invalid_conflict_id PASSED [ 22%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_passes_not_found PASSED [ 33%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_no_overlap PASSED [ 44%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_with_weather_failure PASSED [ 55%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_spacetrack_failure PASSED [ 66%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_llm_failure PASSED [ 77%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_with_alternative_window PASSED [ 88%]
test_recommendations.py::TestRecommendationsEndpoint::test_generate_recommendation_missing_conflict_id PASSED [100%]

========== 9 passed in 3.49s ==========
```

## Adding New Tests

To add new test cases:

1. Create a new test file in `tests/` directory
2. Import necessary fixtures and mocks
3. Follow the naming convention: `test_<feature>.py`
4. Use descriptive test method names: `test_<scenario>_<expected_result>`
5. Add docstrings explaining what each test validates

Example:

```python
def test_new_feature_success(self, client, mock_data):
    """Test successful execution of new feature."""
    response = client.post("/endpoint", json=mock_data)
    assert response.status_code == 200
    assert 'expected_field' in response.json()
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd apps/backend
    source venv/bin/activate
    pytest tests/ -v --tb=short
```

## Troubleshooting

### Import Errors

If you see import errors, ensure PYTHONPATH is set:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Connection Errors

Tests use mock data and don't require a real database. If you see database errors, check that mocks are properly configured.

### Async Test Warnings

Install `pytest-asyncio` to properly handle async tests:

```bash
pip install pytest-asyncio
```

## Future Test Coverage

Planned test suites:

- [ ] `test_passes.py` - Pass calculation endpoint
- [ ] `test_conflicts.py` - Conflict detection endpoint
- [ ] `test_satellites.py` - Satellite listing endpoint
- [ ] `test_ground_stations.py` - Ground station endpoint
- [ ] `test_schedule.py` - Schedule approval endpoint
- [ ] `test_orbit_calc.py` - Orbit calculation service
- [ ] `test_conflict_detector.py` - Conflict detection service
- [ ] `test_llm_reasoner.py` - LLM reasoning service

## Contributing

When adding tests:

1. Ensure all tests pass before committing
2. Maintain >80% code coverage
3. Add docstrings to all test methods
4. Use meaningful assertions with clear error messages
5. Mock external dependencies appropriately
