#!/bin/bash

# Extended Poster Creation Tests
# Tests poster creation with various coordinate sets and parameters

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
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT        API server port (default: $DEFAULT_PORT)"
            echo "  --output-dir DIR   Output directory for test files (default: ./test_outputs)"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  API_BASE_URL       Override base URL (e.g., http://localhost:9000)"
            echo "  OUTPUT_DIR         Output directory (same as --output-dir)"
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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "\n${YELLOW}[TEST]${NC} $1"
}

# Test poster creation with different color schemes
test_different_colors() {
    local colors=("white" "black" "coral" "c")
    
    for color in "${colors[@]}"; do
        log_test "Testing poster creation with color scheme: $color"
        
        local json_data="{
            \"coordinates\": [
                {\"lon\": -74.006, \"lat\": 40.7128},
                {\"lon\": -73.935, \"lat\": 40.7128},
                {\"lon\": -73.935, \"lat\": 40.7589},
                {\"lon\": -74.006, \"lat\": 40.7589}
            ],
            \"city\": \"New York\",
            \"country\": \"United States\",
            \"color\": \"$color\",
            \"width\": 15.0,
            \"dpi\": 300
        }"
        
        local response
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            "$API_BASE_URL/poster" \
            -o "$OUTPUT_DIR/poster_${color}.png" || echo "000")
        
        local status_code=$(echo "$response" | tail -n 1)
        
        if [ "$status_code" = "200" ]; then
            if [ -f "$OUTPUT_DIR/poster_${color}.png" ]; then
                local file_size=$(stat -f%z "$OUTPUT_DIR/poster_${color}.png" 2>/dev/null || stat -c%s "$OUTPUT_DIR/poster_${color}.png" 2>/dev/null || echo "0")
                if [ "$file_size" -gt 0 ]; then
                    log_info "✓ Created poster with color '$color' (${file_size} bytes)"
                else
                    log_error "✗ File created but empty for color '$color'"
                fi
            else
                log_error "✗ No file created for color '$color'"
            fi
        else
            log_error "✗ Failed to create poster with color '$color' (status: $status_code)"
        fi
    done
}

# Test poster creation with different DPI values
test_different_dpi() {
    local dpi_values=(150 300 600)
    
    for dpi in "${dpi_values[@]}"; do
        log_test "Testing poster creation with DPI: $dpi"
        
        local json_data="{
            \"coordinates\": [
                {\"lon\": -74.006, \"lat\": 40.7128},
                {\"lon\": -73.935, \"lat\": 40.7128},
                {\"lon\": -73.935, \"lat\": 40.7589},
                {\"lon\": -74.006, \"lat\": 40.7589}
            ],
            \"city\": \"New York\",
            \"country\": \"United States\",
            \"color\": \"white\",
            \"width\": 15.0,
            \"dpi\": $dpi
        }"
        
        local response
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            "$API_BASE_URL/poster" \
            -o "$OUTPUT_DIR/poster_dpi_${dpi}.png" || echo "000")
        
        local status_code=$(echo "$response" | tail -n 1)
        
        if [ "$status_code" = "200" ]; then
            if [ -f "$OUTPUT_DIR/poster_dpi_${dpi}.png" ]; then
                local file_size=$(stat -f%z "$OUTPUT_DIR/poster_dpi_${dpi}.png" 2>/dev/null || stat -c%s "$OUTPUT_DIR/poster_dpi_${dpi}.png" 2>/dev/null || echo "0")
                log_info "✓ Created poster with DPI $dpi (${file_size} bytes)"
            else
                log_error "✗ No file created for DPI $dpi"
            fi
        else
            log_error "✗ Failed to create poster with DPI $dpi (status: $status_code)"
        fi
    done
}

# Test poster creation with different width values
test_different_widths() {
    local widths=(10.0 15.0 20.0)
    
    for width in "${widths[@]}"; do
        log_test "Testing poster creation with width: $width inches"
        
        local json_data="{
            \"coordinates\": [
                {\"lon\": -74.006, \"lat\": 40.7128},
                {\"lon\": -73.935, \"lat\": 40.7128},
                {\"lon\": -73.935, \"lat\": 40.7589},
                {\"lon\": -74.006, \"lat\": 40.7589}
            ],
            \"city\": \"New York\",
            \"country\": \"United States\",
            \"color\": \"white\",
            \"width\": $width,
            \"dpi\": 300
        }"
        
        local response
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            "$API_BASE_URL/poster" \
            -o "$OUTPUT_DIR/poster_width_${width}.png" || echo "000")
        
        local status_code=$(echo "$response" | tail -n 1)
        
        if [ "$status_code" = "200" ]; then
            if [ -f "$OUTPUT_DIR/poster_width_${width}.png" ]; then
                local file_size=$(stat -f%z "$OUTPUT_DIR/poster_width_${width}.png" 2>/dev/null || stat -c%s "$OUTPUT_DIR/poster_width_${width}.png" 2>/dev/null || echo "0")
                log_info "✓ Created poster with width $width inches (${file_size} bytes)"
            else
                log_error "✗ No file created for width $width"
            fi
        else
            log_error "✗ Failed to create poster with width $width (status: $status_code)"
        fi
    done
}

# Test poster creation with different coordinate regions
test_different_regions() {
    # New York
    local ny_coords='[
        {"lon": -74.006, "lat": 40.7128},
        {"lon": -73.935, "lat": 40.7128},
        {"lon": -73.935, "lat": 40.7589},
        {"lon": -74.006, "lat": 40.7589}
    ]'
    
    # London (smaller area)
    local london_coords='[
        {"lon": -0.1278, "lat": 51.5074},
        {"lon": -0.0759, "lat": 51.5074},
        {"lon": -0.0759, "lat": 51.5200},
        {"lon": -0.1278, "lat": 51.5200}
    ]'
    
    # Moscow (smaller area)
    local moscow_coords='[
        {"lon": 37.6173, "lat": 55.7558},
        {"lon": 37.6719, "lat": 55.7558},
        {"lon": 37.6719, "lat": 55.7878},
        {"lon": 37.6173, "lat": 55.7878}
    ]'
    
    local regions=(
        "New York|United States|$ny_coords"
        "London|United Kingdom|$london_coords"
        "Moscow|Russia|$moscow_coords"
    )
    
    for region_info in "${regions[@]}"; do
        IFS='|' read -r city country coords <<< "$region_info"
        log_test "Testing poster creation for: $city, $country"
        
        local json_data="{
            \"coordinates\": $coords,
            \"city\": \"$city\",
            \"country\": \"$country\",
            \"color\": \"white\",
            \"width\": 15.0,
            \"dpi\": 300
        }"
        
        local safe_city=$(echo "$city" | tr ' ' '_' | tr -d ',')
        local response
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            "$API_BASE_URL/poster" \
            -o "$OUTPUT_DIR/poster_${safe_city}.png" || echo "000")
        
        local status_code=$(echo "$response" | tail -n 1)
        
        if [ "$status_code" = "200" ]; then
            if [ -f "$OUTPUT_DIR/poster_${safe_city}.png" ]; then
                local file_size=$(stat -f%z "$OUTPUT_DIR/poster_${safe_city}.png" 2>/dev/null || stat -c%s "$OUTPUT_DIR/poster_${safe_city}.png" 2>/dev/null || echo "0")
                log_info "✓ Created poster for $city (${file_size} bytes)"
            else
                log_error "✗ No file created for $city"
            fi
        else
            log_error "✗ Failed to create poster for $city (status: $status_code)"
        fi
    done
}

# Main execution
main() {
    log_info "Starting extended poster creation tests"
    log_info "API: $API_BASE_URL"
    log_info "Output directory: $OUTPUT_DIR"
    
    # Check if API is running
    local health_response
    health_response=$(curl -s -w "\n%{http_code}" "$API_BASE_URL/health" || echo "000")
    local status_code=$(echo "$health_response" | tail -n 1)
    
    if [ "$status_code" != "200" ]; then
        log_error "API is not responding at $API_BASE_URL/health"
        exit 1
    fi
    
    log_info "API is responding, starting tests...\n"
    
    test_different_colors
    test_different_dpi
    test_different_widths
    test_different_regions
    
    log_info "\nExtended tests completed!"
    log_info "Check $OUTPUT_DIR for generated poster files"
}

main "$@"

