# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for geospatial libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Set default data directory
ENV MAPOC_DATA_DIR=/root/.mapoc

# Build argument to disable tiny mode (default: use tiny mode)
ARG NO_TINY=false

# Build argument to specify external data directory (skips setup.sh)
# If set, files will be copied from this directory (relative to build context) instead of downloading
# Note: Files are copied at build time and baked into the image.
#       If the source directory changes, rebuild the image to pick up changes.
ARG DATA_DIR=

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package in development mode
RUN pip install --no-cache-dir -e .

# Create data directory
RUN mkdir -p /root/.mapoc

# Handle data directory setup
# Priority: 1) DATA_DIR build arg, 2) .mapoc in build context, 3) run setup.sh
# Note: DATA_DIR must be relative to build context. Files are copied at build time.
#       If the source directory changes after build, rebuild the image to pick up changes.
RUN DATA_COPIED=false; \
    if [ -n "$DATA_DIR" ] && [ "$DATA_DIR" != "" ]; then \
        echo "Using external data directory: $DATA_DIR"; \
        echo "Current directory: $(pwd)"; \
        echo "Checking if directory exists..."; \
        if [ -d "$DATA_DIR" ]; then \
            echo "Directory found: $DATA_DIR"; \
            echo "Copying data files from $DATA_DIR to /root/.mapoc..."; \
            if [ -n "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then \
                cp -r "$DATA_DIR"/. /root/.mapoc/ 2>&1 || cp -r "$DATA_DIR"/* /root/.mapoc/ 2>&1 || true; \
                echo "Data files copied. Skipping setup.sh."; \
                DATA_COPIED=true; \
            else \
                echo "WARNING: DATA_DIR is empty, will run setup.sh instead."; \
            fi; \
        else \
            echo "ERROR: DATA_DIR specified but directory does not exist: $DATA_DIR"; \
            echo "Note: DATA_DIR must be relative to the Docker build context."; \
            echo "Available files/directories:"; \
            ls -la || true; \
            echo "Falling back to checking .mapoc in build context..."; \
        fi; \
    fi; \
    if [ "$DATA_COPIED" = "false" ] && [ -d .mapoc ]; then \
        echo "Found .mapoc directory in build context, copying to container..."; \
        if [ -n "$(ls -A .mapoc 2>/dev/null)" ]; then \
            cp -r .mapoc/. /root/.mapoc/ 2>&1 || cp -r .mapoc/* /root/.mapoc/ 2>&1 || true; \
            echo "Data files copied from build context."; \
            DATA_COPIED=true; \
        else \
            echo "WARNING: .mapoc directory is empty, will run setup.sh instead."; \
        fi; \
    fi; \
    if [ "$DATA_COPIED" = "false" ]; then \
        echo "No data directory found, will run setup.sh to download data..."; \
    fi

# Run setup.sh to download data files if they don't already exist
# Skip if DATA_DIR was provided (files already copied above)
# Use --tiny by default (only region tree), unless NO_TINY is set
# Use --skip-colors to avoid interactive prompt during build
RUN if [ -n "$DATA_DIR" ]; then \
        echo "Skipping setup.sh (using external DATA_DIR)"; \
    elif [ "$NO_TINY" = "true" ] || [ "$NO_TINY" = "1" ]; then \
        echo "Running full setup (NO_TINY=true)..."; \
        # Check if key files exist before running full setup \
        if [ ! -f /root/.mapoc/countries.csv ] || [ ! -f /root/.mapoc/cities_geonames_1000.csv ] || \
           [ ! -f /root/.mapoc/geofabrik_tree.nw ] || [ ! -f /root/.mapoc/geoBoundariesCGAZ_ADM2.geojson ]; then \
            chmod +x scripts/setup.sh && \
            bash scripts/setup.sh --skip-colors; \
        else \
            echo "Required data files already exist, skipping setup.sh"; \
        fi; \
    else \
        echo "Running tiny setup (minimal data, coordinate-based only)..."; \
        # Check if region tree exists before running tiny setup \
        if [ ! -f /root/.mapoc/geofabrik_tree.nw ]; then \
            chmod +x scripts/setup.sh && \
            bash scripts/setup.sh --tiny --skip-colors; \
        else \
            echo "Region tree already exists, skipping setup.sh"; \
        fi; \
    fi

# Create necessary directories
RUN mkdir -p /app/data /app/output

# Expose the API port
EXPOSE 8000

# Set environment variable for uvicorn
ENV PYTHONUNBUFFERED=1

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "map_poster_creator.api:app", "--host", "0.0.0.0", "--port", "8000"]

