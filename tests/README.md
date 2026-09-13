# API Tests

This directory contains bash-based integration tests for the Map Poster Creator API using `curl`.

## Test Files

- **`test_api.sh`** - Main test suite covering all API endpoints with validation tests
- **`test_posters.sh`** - Extended tests for poster creation with various parameters
- **`run_all_tests.sh`** - Convenience script to run all tests interactively
- **`example_poster_request.json`** - Example JSON for POST /poster endpoint
- **`example_poster_simple_request.json`** - Example JSON for POST /poster/simple endpoint

## Prerequisites

1. The API server must be running:
   ```bash
   uvicorn map_poster_creator.api:app --host 0.0.0.0 --port 8000
   ```

2. Make the test scripts executable:
   ```bash
   chmod +x tests/test_api.sh
   chmod +x tests/test_posters.sh
   ```

## Running Tests

### Basic API Tests

Run the main test suite:

```bash
./tests/test_api.sh
```

This will test:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /colors` - List color schemes
- `POST /poster` - Poster creation (validation and basic functionality)
- `POST /poster/simple` - Simplified poster endpoint

### Extended Poster Tests

Run extended tests for poster creation with various parameters:

```bash
./tests/test_posters.sh
```

### Run All Tests

Use the convenience script to run all tests:

```bash
./tests/run_all_tests.sh
```

This will run the basic API tests and optionally prompt you to run extended tests.

This will test:
- Different color schemes
- Different DPI values
- Different width values
- Different geographic regions

## Configuration

You can configure the tests using command-line arguments or environment variables:

### Command-Line Arguments

```bash
# Specify port
./tests/test_api.sh --port 8000

# Enable verbose output
./tests/test_api.sh --verbose

# Change output directory
./tests/test_api.sh --output-dir ./my_outputs

# Combine options
./tests/test_api.sh --port 9000 --verbose --output-dir ./test_outputs

# Show help
./tests/test_api.sh --help
```

### Environment Variables

```bash
# Change API base URL (overrides --port)
export API_BASE_URL="http://localhost:9000"

# Enable verbose output (same as --verbose)
export VERBOSE="true"

# Change output directory (same as --output-dir)
export OUTPUT_DIR="./test_outputs"

# Run tests
./tests/test_api.sh
```

## Test Output

- Test results are printed to stdout with color-coded output
- Generated poster images are saved to `test_outputs/` directory (or `$OUTPUT_DIR`)
- JSON responses are saved for reference (e.g., `colors_response.json`)

## Expected Behavior

### Tests That Should Always Pass

- Root endpoint (`GET /`)
- Health check (`GET /health`)
- List colors (`GET /colors`)
- Validation tests (invalid inputs should return 400/422)

### Tests That May Fail Without Data

- Poster creation tests may fail if:
  - SHP (shapefile) data is not available for the requested region
  - The API cannot automatically determine the correct regional dataset
  - Required data files are missing

These failures are expected in environments without full data setup and are handled gracefully by the tests.

## Example Usage

```bash
# Run all basic tests (default port 8000)
./tests/test_api.sh

# Run with custom port
./tests/test_api.sh --port 9000

# Run with verbose output
./tests/test_api.sh --verbose
# or
VERBOSE=true ./tests/test_api.sh

# Run against a different server using environment variable
API_BASE_URL=http://localhost:9000 ./tests/test_api.sh

# Run extended poster tests with custom port
./tests/test_posters.sh --port 8000

# Run all tests interactively with custom port
./tests/run_all_tests.sh --port 8000

# Manual testing with example JSON files
curl -X POST http://localhost:8000/poster \
  -H "Content-Type: application/json" \
  -d @tests/example_poster_request.json \
  -o poster.png

curl -X POST http://localhost:8000/poster/simple \
  -H "Content-Type: application/json" \
  -d @tests/example_poster_simple_request.json \
  -o poster_simple.png
```

## Test Coverage

The tests cover:

1. **Endpoint Availability**: All endpoints respond correctly
2. **Input Validation**: Invalid inputs are properly rejected
3. **Error Handling**: Appropriate HTTP status codes are returned
4. **Response Format**: JSON responses match expected structure
5. **File Generation**: Poster images are created when data is available
6. **Parameter Variations**: Different parameter combinations work correctly

## Troubleshooting

### API Not Responding

If tests fail with "API is not responding":
- Ensure the API server is running
- Check the port (default: 8000)
- Verify `API_BASE_URL` environment variable if using a different URL

### Poster Creation Fails

If poster creation tests fail:
- This may be expected if SHP data is not available
- Check API logs for specific error messages
- Ensure required data files are present if testing with specific regions

### Permission Errors

If you get permission errors:
```bash
chmod +x tests/*.sh
```
