#!/bin/bash
set -e

# Set environment variables (in case they're not set)
# These must be set before Python imports config, so set them early
export MAPOC_DATA_DIR="${MAPOC_DATA_DIR:-/app/data}"
export MAPOC_OUTPUT_DIR="${MAPOC_OUTPUT_DIR:-/app/output}"

# Ensure the directories exist
mkdir -p "$MAPOC_DATA_DIR" "$MAPOC_OUTPUT_DIR"

# Function to check if data directory exists and has required files
check_data_directory() {
    local dir="$1"
    if [ -d "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null)" ] && \
       [ -f "${dir}/geofabrik_tree.nw" ]; then
        return 0
    fi
    return 1
}

# Function to prepare data directory using setup.sh
prepare_data_directory() {
    local output_dir="$1"
    echo "Data directory missing or incomplete. Creating it..."
    
    if [ ! -f "/app/scripts/setup.sh" ]; then
        echo "Error: setup.sh not found at /app/scripts/setup.sh"
        return 1
    fi
    
    mkdir -p "$output_dir"
    chmod +x /app/scripts/setup.sh
    
    # Run setup.sh in tiny mode to create data
    if /app/scripts/setup.sh --tiny --skip-colors --non-interactive --output "$output_dir"; then
        echo "Data directory created successfully: $output_dir"
        return 0
    else
        echo "Warning: setup.sh failed to create data directory"
        return 1
    fi
}

# Check for data sources in priority order:
# 1) /app/data_source (created during build from host data/ or setup.sh)
# 2) /app/data (from build context or volume mount)
# 3) Run setup.sh to create it in /app/data
# 4) Fallback to old locations
DATA_SOURCE=""

if check_data_directory "/app/data_source"; then
    echo "Using data from build: /app/data_source"
    DATA_SOURCE="/app/data_source"
elif check_data_directory "$MAPOC_DATA_DIR"; then
    echo "Using existing data directory: $MAPOC_DATA_DIR"
    DATA_SOURCE="$MAPOC_DATA_DIR"
else
    # Try to create data directory in MAPOC_DATA_DIR
    if prepare_data_directory "$MAPOC_DATA_DIR"; then
        if check_data_directory "$MAPOC_DATA_DIR"; then
            DATA_SOURCE="$MAPOC_DATA_DIR"
        fi
    fi
    
    # If still no data, try fallback locations
    if [ -z "$DATA_SOURCE" ]; then
        if check_data_directory "/app/data_built"; then
            DATA_SOURCE="/app/data_built"
            echo "Using fallback data from: /app/data_built"
        elif check_data_directory "/root/.mapoc"; then
            DATA_SOURCE="/root/.mapoc"
            echo "Using fallback data from: /root/.mapoc"
        else
            echo "Warning: No data source found. Application may not work correctly."
        fi
    fi
fi

# Copy data to MAPOC_DATA_DIR if we have a source and target is empty or missing key files
if [ -n "$DATA_SOURCE" ] && [ "$DATA_SOURCE" != "$MAPOC_DATA_DIR" ]; then
    if ! check_data_directory "$MAPOC_DATA_DIR"; then
        echo "Copying data from $DATA_SOURCE to $MAPOC_DATA_DIR..."
        mkdir -p "$MAPOC_DATA_DIR"
        cp -r "$DATA_SOURCE"/* "$MAPOC_DATA_DIR"/ 2>/dev/null || true
        echo "Data copied successfully to $MAPOC_DATA_DIR"
    else
        echo "Data directory $MAPOC_DATA_DIR already contains required files."
    fi
fi

# Final verification: ensure geofabrik_tree.nw exists where expected
if [ ! -f "$MAPOC_DATA_DIR/geofabrik_tree.nw" ]; then
    echo "WARNING: geofabrik_tree.nw not found in $MAPOC_DATA_DIR"
    echo "Expected location: $MAPOC_DATA_DIR/geofabrik_tree.nw"
    echo "This may cause runtime errors."
else
    echo "✓ Verified: geofabrik_tree.nw exists at $MAPOC_DATA_DIR/geofabrik_tree.nw"
fi

# Start the application
exec "$@"

