#!/bin/bash

# Convenience script to run all API tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default configuration
DEFAULT_PORT=8000

# Parse command-line arguments
PORT="$DEFAULT_PORT"
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            EXTRA_ARGS+=("--port" "$2")
            shift 2
            ;;
        --verbose|-v)
            EXTRA_ARGS+=("--verbose")
            shift
            ;;
        --output-dir)
            EXTRA_ARGS+=("--output-dir" "$2")
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT        API server port (default: $DEFAULT_PORT)"
            echo "  --verbose, -v      Enable verbose output"
            echo "  --output-dir DIR   Output directory for test files (default: ./test_outputs)"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  API_BASE_URL       Override base URL (e.g., http://localhost:9000)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set API base URL (allow environment variable to override)
API_BASE_URL="${API_BASE_URL:-http://localhost:${PORT}}"

echo "========================================="
echo "Map Poster Creator API - Test Suite"
echo "========================================="
echo ""

echo "Checking API at $API_BASE_URL..."

if ! curl -s -f "$API_BASE_URL/health" > /dev/null 2>&1; then
    echo "ERROR: API is not responding at $API_BASE_URL/health"
    echo ""
    echo "Please start the API server first:"
    echo "  uvicorn map_poster_creator.api:app --host 0.0.0.0 --port $PORT"
    exit 1
fi

echo "✓ API is responding"
echo ""

# Run basic API tests
echo "Running basic API tests..."
echo "----------------------------------------"
./test_api.sh "${EXTRA_ARGS[@]}"

echo ""
echo "========================================="
echo ""

# Ask if user wants to run extended tests
read -p "Run extended poster creation tests? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running extended poster tests..."
    echo "----------------------------------------"
    ./test_posters.sh "${EXTRA_ARGS[@]}"
fi

echo ""
echo "========================================="
echo "All tests completed!"
echo "========================================="
