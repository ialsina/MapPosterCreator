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

# Copy DATA_DIR if provided (using a workaround for conditional COPY)
# Create a temporary directory that will be used if DATA_DIR is provided
RUN mkdir -p /tmp/data-source

# Copy DATA_DIR if provided (this will be a no-op if DATA_DIR is empty due to .dockerignore)
# Note: To use DATA_DIR, create a .dockerignore that doesn't exclude it, or structure your build differently
# For now, we'll handle it in the RUN command below

# Run setup.sh or copy from DATA_DIR
# Copy data from /root/.mapoc to /app/data_built for volume mounting support
RUN if [ -n "$DATA_DIR" ] && [ -d "$DATA_DIR" ]; then \
        echo "Using DATA_DIR=$DATA_DIR"; \
        cp -r "$DATA_DIR"/* /root/.mapoc/ 2>/dev/null || true; \
        mkdir -p /app/data_built && \
        cp -r /root/.mapoc/* /app/data_built/ 2>/dev/null || true; \
    elif [ "$NO_TINY" = "true" ] || [ "$NO_TINY" = "1" ]; then \
        echo "Running setup.sh in full mode (NO_TINY=true)"; \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --skip-colors --non-interactive && \
        mkdir -p /app/data_built && \
        cp -r /root/.mapoc/* /app/data_built/ 2>/dev/null || true; \
    else \
        echo "Running setup.sh in tiny mode (default)"; \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --tiny --skip-colors --non-interactive && \
        mkdir -p /app/data_built && \
        cp -r /root/.mapoc/* /app/data_built/ 2>/dev/null || true; \
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

