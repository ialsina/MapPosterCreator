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

# Copy DATA_DIR if provided
COPY ${DATA_DIR} /tmp/data-source/

# Copy data files to /root/.mapoc
RUN if [ -d /tmp/data-source ]; then \
        cp -r /tmp/data-source/* /root/.mapoc/ && \
        rm -rf /tmp/data-source; \
    fi

# Run setup.sh if DATA_DIR was not provided
RUN if [ -n "$DATA_DIR" ]; then \
        echo "Skipping setup.sh (using DATA_DIR=$DATA_DIR)"; \
    elif [ "$NO_TINY" = "true" ] || [ "$NO_TINY" = "1" ]; then \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --skip-colors; \
    else \
        chmod +x scripts/setup.sh && \
        bash scripts/setup.sh --tiny --skip-colors; \
    fi

# Create necessary directories
RUN mkdir -p /app/data /app/output

# Expose the API port
EXPOSE 8000

# Set environment variable for uvicorn
ENV PYTHONUNBUFFERED=1

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "map_poster_creator.api:app", "--host", "0.0.0.0", "--port", "8000"]

