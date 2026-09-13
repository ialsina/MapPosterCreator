#!/bin/bash

# Simple test script for Map Poster Creator API
# Sends polygon coordinates and optional color scheme, saves output PNG

set -euo pipefail

# Default configuration
DEFAULT_PORT=8000
OUTPUT_DIR="${OUTPUT_DIR:-./test_outputs}"

# Parse command-line arguments
PORT="$DEFAULT_PORT"
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT        API server port (default: $DEFAULT_PORT)"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  COLOR              Color scheme name (default: white)"
            echo "  OUTPUT_DIR         Output directory (default: ./test_outputs)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set API URL
API_URL="http://localhost:${PORT}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Simple polygon coordinates: a small square around New York
# Format: [[lon, lat], [lon, lat], ...]
COORDINATES='[
    [-74.006, 40.7128],
    [-73.935, 40.7128],
    [-73.935, 40.7589],
    [-74.006, 40.7589]
]'

# Optional color scheme (defaults to "white" if not provided)
COLOR_SCHEME="${COLOR:-white}"

# Create JSON request body (without city or country)
JSON_BODY=$(cat <<EOF
{
    "coordinates": $COORDINATES,
    "color": "$COLOR_SCHEME"
}
EOF
)

# Output file
OUTPUT_FILE="$OUTPUT_DIR/poster.png"

echo "Testing Map Poster Creator API"
echo "API URL: $API_URL"
echo "Output file: $OUTPUT_FILE"
echo ""

# Make POST request and save PNG
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$OUTPUT_FILE" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$JSON_BODY" \
    "$API_URL/poster/simple")

echo "HTTP Status: $HTTP_CODE"

# Check HTTP status
if [ "$HTTP_CODE" != "200" ]; then
    echo "✗ Error: API returned status code $HTTP_CODE"
    if [ -f "$OUTPUT_FILE" ]; then
        echo "Response body:"
        cat "$OUTPUT_FILE"
        echo ""
    fi
    exit 1
fi

# Check if file was created
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "✗ Error: Output file was not created"
    exit 1
fi

# Check file size
FILE_SIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || stat -f%z "$OUTPUT_FILE" 2>/dev/null || echo "0")
if [ "$FILE_SIZE" -eq 0 ]; then
    echo "✗ Error: Output file is empty"
    exit 1
fi

# Validate that it's a valid PNG image
if command -v file >/dev/null 2>&1; then
    FILE_TYPE=$(file -b "$OUTPUT_FILE")
    if echo "$FILE_TYPE" | grep -qi "PNG image"; then
        echo "✓ Valid PNG image detected"
    else
        echo "✗ Error: Output is not a valid PNG image"
        echo "File type: $FILE_TYPE"
        exit 1
    fi
else
    # Fallback: check PNG magic bytes (89 50 4E 47 0D 0A 1A 0A)
    FIRST_BYTES=$(head -c 8 "$OUTPUT_FILE" | od -An -tx1 | tr -d ' \n')
    if [ "$FIRST_BYTES" = "89504e470d0a1a0a" ]; then
        echo "✓ Valid PNG image detected (magic bytes check)"
    else
        echo "✗ Error: Output does not have PNG magic bytes"
        echo "First bytes: $FIRST_BYTES"
        exit 1
    fi
fi

echo "✓ Success! Poster saved to $OUTPUT_FILE (${FILE_SIZE} bytes)"
exit 0
