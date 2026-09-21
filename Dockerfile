# MapPosterCreator – built image is tagged at build time (e.g. by Compose or GitHub Actions).
# Convention: ghcr.io/<owner>/<image>:<tag> (GitHub Container Registry).
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

# Set default data directory (will be overridden by docker-entrypoint.sh if needed)
# The entrypoint script will ensure data is in /app/data
ENV MAPOC_DATA_DIR=/app/data
ENV MAPOC_OUTPUT_DIR=/app/output
ENV MAPOC_KEEP_SHP_FILES=true
ENV LOG_DIR=/app/logs

# Build argument: pass TINY=true for coordinates-only setup (default is full geographic data)
ARG TINY=false
ENV TINY=${TINY}

# Build argument to specify external data directory (skips setup.sh)
# If set, files will be copied from this directory (relative to build context) instead of downloading
# Note: Files are copied at build time and baked into the image.
#       If the source directory changes, rebuild the image to pick up changes.
ARG DATA_DIR=

# Copy the application code and install runtime dependencies from pyproject.toml
COPY . .

RUN pip install --no-cache-dir -e .

# Create data directory
RUN mkdir -p /root/.mapoc

# Handle data directory: use data/ from build context if exists, otherwise create it
# Create necessary directories first
RUN mkdir -p /app/data_source

# Handle data directory: use copied data/, DATA_DIR arg, or run setup.sh
# Note: data/ is already copied by "COPY . ." above if it exists in build context
# Priority: 1) data/ from build context, 2) DATA_DIR arg, 3) run setup.sh
RUN if [ -d "/app/data" ] && [ -n "$(ls -A /app/data 2>/dev/null)" ] && \
       [ -f "/app/data/geofabrik_tree.nw" ] 2>/dev/null && \
       [ -f "/app/data/cities_geonames_1000.csv" ] 2>/dev/null && \
       [ -f "/app/data/countries.csv" ] 2>/dev/null; then \
        echo "Using data/ directory from build context (host)"; \
        cp -r /app/data/* /app/data_source/ 2>/dev/null || true; \
        echo "Data copied from host data/ directory to /app/data_source"; \
    elif [ -n "$DATA_DIR" ] && [ -d "$DATA_DIR" ]; then \
        echo "Using DATA_DIR=$DATA_DIR"; \
        cp -r "$DATA_DIR"/* /app/data_source/ 2>/dev/null || true; \
    elif [ "$TINY" = "true" ] || [ "$TINY" = "1" ]; then \
        echo "data/ not found in build context. Running setup.sh in tiny mode (TINY=true)"; \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --tiny --non-interactive --output /app/data_source && \
        echo "Data created in /app/data_source"; \
    else \
        echo "data/ not found in build context. Running setup.sh in full mode (default)"; \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --non-interactive --output /app/data_source && \
        echo "Data created in /app/data_source"; \
    fi

# Ensure docc_colors.json exists (full non-interactive setup skips it in setup.sh)
RUN if [ ! -f "/app/data_source/docc_colors.json" ]; then \
        echo "Generating docc_colors.json..."; \
        MAPOC_DATA_DIR=/app/data_source python3 /app/scripts/fetch_docc_colors.py; \
    else \
        echo "docc_colors.json already present in data source"; \
    fi

# Create necessary directories
RUN mkdir -p /app/data /app/output /app/logs

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Expose the API port
EXPOSE 8000

# Set environment variable for uvicorn
ENV PYTHONUNBUFFERED=1

# Add healthcheck to verify the service is ready
# Uses the /health endpoint which checks if data is loaded
# start-period allows time for initial data loading and startup
HEALTHCHECK --interval=10s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request, json, sys; \
    response = urllib.request.urlopen('http://localhost:8000/health'); \
    data = json.loads(response.read()); \
    sys.exit(0 if data.get('data_ready') else 1)" || exit 1

# Use entrypoint to handle data copying
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "map_poster_creator.api:app", "--host", "0.0.0.0", "--port", "8000"]
