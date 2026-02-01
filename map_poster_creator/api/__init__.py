"""
FastAPI application for creating map posters from polygon coordinates.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI

from map_poster_creator.api.endpoints import register_endpoints

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_dir = Path(os.getenv("LOG_DIR", "/app/logs"))
log_dir.mkdir(parents=True, exist_ok=True)

# Set up file handler for detailed logs
log_file = log_dir / "map_poster_api.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(file_formatter)

# Set up console handler for basic output
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, log_level, logging.INFO))
console_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(console_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured. Log file: {log_file}")

app = FastAPI(
    title="Map Poster Creator API",
    description="API for creating map posters from polygon coordinates",
    version="0.8.0",
)

# Register all endpoints
register_endpoints(app)

# Make app available for uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
