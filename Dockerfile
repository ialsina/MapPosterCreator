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

# Handle data directory: use data/ from build context if exists, otherwise create it
# Create necessary directories first
RUN mkdir -p /app/data_source

# Handle data directory: use copied data/, DATA_DIR arg, or run setup.sh
# Note: data/ is already copied by "COPY . ." above if it exists in build context
# Priority: 1) data/ from build context, 2) DATA_DIR arg, 3) run setup.sh
RUN if [ -d "/app/data" ] && [ -n "$(ls -A /app/data 2>/dev/null)" ] && \
       [ -f "/app/data/geofabrik_tree.nw" ] 2>/dev/null; then \
        echo "Using data/ directory from build context (host)"; \
        cp -r /app/data/* /app/data_source/ 2>/dev/null || true; \
        echo "Data copied from host data/ directory to /app/data_source"; \
    elif [ -n "$DATA_DIR" ] && [ -d "$DATA_DIR" ]; then \
        echo "Using DATA_DIR=$DATA_DIR"; \
        cp -r "$DATA_DIR"/* /app/data_source/ 2>/dev/null || true; \
    elif [ "$NO_TINY" = "true" ] || [ "$NO_TINY" = "1" ]; then \
        echo "data/ not found in build context. Running setup.sh in full mode (NO_TINY=true)"; \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --skip-colors --non-interactive --output /app/data_source && \
        echo "Data created in /app/data_source"; \
    else \
        echo "data/ not found in build context. Running setup.sh in tiny mode (default)"; \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --tiny --skip-colors --non-interactive --output /app/data_source && \
        echo "Data created in /app/data_source"; \
    fi

# Create necessary directories
RUN mkdir -p /app/data /app/output

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Expose the API port
EXPOSE 8000

# Set environment variable for uvicorn
ENV PYTHONUNBUFFERED=1

# Use entrypoint to handle data copying
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "map_poster_creator.api:app", "--host", "0.0.0.0", "--port", "8000"]

