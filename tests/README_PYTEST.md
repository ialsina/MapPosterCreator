# Pytest Test Suite

This directory contains comprehensive pytest-based unit tests for the Map Poster Creator project.

## Test Structure

- **`conftest.py`** - Shared pytest fixtures and utilities
- **`test_api_endpoints.py`** - Tests for all API endpoints (`/`, `/health`, `/colors`, `/poster`, `/poster/simple`)
- **`test_api_utils.py`** - Tests for API utility functions
- **`test_data_core.py`** - Tests for `map_poster_creator/data/core.py` functions
- **`test_core.py`** - Tests for `map_poster_creator/core.py` functions

## Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-mock` - Enhanced mocking capabilities

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=map_poster_creator --cov-report=html --cov-report=term
```

This will:
- Generate a terminal coverage report
- Generate an HTML coverage report in `htmlcov/` directory

### Run Specific Test Files

```bash
# Test API endpoints only
pytest tests/test_api_endpoints.py

# Test data core functions only
pytest tests/test_data_core.py

# Test core functions only
pytest tests/test_core.py

# Test API utils only
pytest tests/test_api_utils.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_api_endpoints.py::TestRootEndpoint

# Run a specific test function
pytest tests/test_api_endpoints.py::TestRootEndpoint::test_root_endpoint
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Detailed Output

```bash
pytest -vv
```

### Run Tests and Stop on First Failure

```bash
pytest -x
```

## Test Coverage

The test suite aims for comprehensive coverage of:

1. **API Endpoints** (`map_poster_creator/api/endpoints.py`):
   - Root endpoint (`GET /`)
   - Health check (`GET /health`)
   - List colors (`GET /colors`)
   - Create poster (`POST /poster`)
   - Create poster simple (`POST /poster/simple`)
   - Various error cases and edge cases
   - Different parameter combinations (DPI, width, colors)

2. **API Utils** (`map_poster_creator/api/utils.py`):
   - `find_shp_from_polygon` with various scenarios
   - City resolution fallbacks
   - Centroid-based SHP finding

3. **Data Core** (`map_poster_creator/data/core.py`):
   - `resolve_city` with different parameters
   - `get_geojson_path_from_geoboundaries` with various options
   - `find_download_shp_from_point` with different modes
   - `find_download_shp` with various configurations
   - Helper functions (`_extract_shp_url`, `_calculate_point_choose`)

4. **Core** (`map_poster_creator/core.py`):
   - `create_poster` from polygon and GeoJSON
   - `create_poster_from_coordinates` with various formats
   - `_get_boundary_shape` with different input types
   - `_preprocessing` and `_preprocessing_roads` functions
   - Different DPI and width combinations

## Test Fixtures

The `conftest.py` file provides reusable fixtures:

- `client` - FastAPI test client
- `temp_dir` - Temporary directory for test files
- `sample_polygon` - Sample polygon geometry
- `sample_point` - Sample point geometry
- `sample_coordinates` - Sample coordinate list
- `mock_city_series` - Mock city data Series
- `mock_city_df` - Mock city DataFrame
- `mock_country_df` - Mock country DataFrame
- `mock_region_node` - Mock region tree node
- `mock_geofabrik_urls` - Mock GeoFabrik URLs
- `mock_shp_dir` - Mock SHP directory with dummy files
- `mock_geodataframe` - Mock GeoDataFrame
- `mock_colorscheme` - Mock color scheme
- `mock_colorschemes` - Mock color schemes dictionary
- `mock_paths` - Mock paths configuration

## Configuration

Test configuration is in `pytest.ini` at the project root:

- Test discovery patterns
- Coverage settings (minimum 70% coverage)
- Markers for test categorization
- Asyncio mode configuration
- Warning filters

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The coverage threshold is set to 70%, but can be adjusted in `pytest.ini`.

## Notes

- Tests use mocking extensively to avoid external dependencies (file system, network calls, etc.)
- Some tests may require actual data files for full integration testing
- The test suite focuses on unit testing with mocked dependencies
- For integration tests, see the bash-based tests in `test_api.sh` and `test_posters.sh`

## Troubleshooting

### Import Errors

If you encounter import errors, ensure you're running tests from the project root:

```bash
cd /path/to/MapPosterCreator
pytest
```

### Coverage Not Working

Make sure `pytest-cov` is installed:

```bash
pip install pytest-cov
```

### Async Test Issues

Ensure `pytest-asyncio` is installed and the asyncio mode is set correctly in `pytest.ini`.
