#!/bin/bash
set -e

# Set environment variables (in case they're not set)
export MAPOC_DATA_DIR="${MAPOC_DATA_DIR:-/app/data}"
export MAPOC_OUTPUT_DIR="${MAPOC_OUTPUT_DIR:-/app/output}"

# If /app/data is empty (volume mount), copy data from built-in location
# Try /app/data_built first, then /root/.mapoc as fallback
DATA_SOURCE=""
if [ -d "/app/data_built" ] && [ -n "$(ls -A /app/data_built 2>/dev/null)" ]; then
    DATA_SOURCE="/app/data_built"
elif [ -d "/root/.mapoc" ] && [ -n "$(ls -A /root/.mapoc 2>/dev/null)" ]; then
    DATA_SOURCE="/root/.mapoc"
fi

if [ -n "$DATA_SOURCE" ]; then
    # Check if data directory is empty or missing key files
    if [ -z "$(ls -A /app/data 2>/dev/null)" ] || \
       [ ! -f "/app/data/geofabrik_tree.nw" ] || \
       ([ "$NO_TINY" != "true" ] && [ ! -f "/app/data/cities_geonames_1000.csv" ]); then
        echo "Data directory is empty or missing key files. Copying built-in data from $DATA_SOURCE..."
        mkdir -p /app/data
        cp -r "$DATA_SOURCE"/* /app/data/ 2>/dev/null || true
        echo "Data copied successfully."
    else
        echo "Data directory already contains required files."
    fi
else
    echo "Warning: Built-in data directory not found. Data may need to be downloaded."
fi

# Start the application
exec "$@"

