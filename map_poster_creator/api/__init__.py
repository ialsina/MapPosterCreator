"""
FastAPI application for creating map posters from polygon coordinates.
"""

import logging
import os
import time
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


@app.on_event("startup")
async def startup_event():
    """
    Startup event to check data availability.

    This runs in the background and doesn't block server startup.
    The health endpoint will report the actual status.
    """
    import asyncio

    async def check_data_availability():
        """Background task to validate data without blocking server startup."""
        logger.info("Starting background data availability check...")

        # Import here to avoid circular imports and to ensure paths are set
        from map_poster_creator.config import paths

        # Check for required data files
        required_files = [
            paths.geofabrik_tree_nw,
            paths.geofabrik_urls,
        ]

        max_wait = 30  # seconds
        check_interval = 0.5  # seconds
        waited = 0

        while waited < max_wait:
            all_ready = True
            missing_files = []

            for file_path in required_files:
                if not file_path.exists():
                    all_ready = False
                    missing_files.append(str(file_path))
                elif file_path.stat().st_size == 0:
                    # File exists but is empty - still being copied
                    all_ready = False
                    missing_files.append(f"{file_path} (empty)")
                elif file_path == paths.geofabrik_tree_nw:
                    # Check if file is suspiciously small (might be corrupted)
                    file_size = file_path.stat().st_size
                    if (
                        file_size < 50000
                    ):  # Less than 50KB is suspicious (should be ~4MB)
                        logger.warning(
                            f"geofabrik_tree.nw is suspiciously small ({file_size} bytes). Expected ~4MB."
                        )
                        all_ready = False
                        missing_files.append(
                            f"{file_path} (too small: {file_size} bytes)"
                        )

            if all_ready:
                # Additional check: try to load the regions tree to ensure it's valid
                try:
                    logger.info("Data files found, validating regions tree...")
                    from map_poster_creator.data.getters import get_regions_tree

                    tree = get_regions_tree()
                    node_count = len(list(tree.traverse()))
                    logger.info(
                        f"✓ Successfully loaded regions tree with {node_count} nodes"
                    )
                    logger.info("✓ API startup complete - ready to accept requests")
                    return
                except Exception as e:
                    logger.warning(
                        f"Regions tree validation failed (attempt {int(waited/check_interval)+1}): {e}"
                    )
                    # Clear the cache so it can retry
                    from map_poster_creator.data.models import _regions_tree

                    _regions_tree.clear_cache()
                    all_ready = False

            if not all_ready:
                if waited == 0:
                    logger.info(
                        f"Waiting for data files to be ready: {', '.join(missing_files) if missing_files else 'validating...'}"
                    )
                await asyncio.sleep(check_interval)
                waited += check_interval

        # If we get here, we've waited too long
        logger.error(
            f"Timeout waiting for data files after {max_wait}s. Missing or invalid: {', '.join(missing_files) if missing_files else 'validation failed'}"
        )
        logger.error(
            "API started but may not function correctly. Check /health endpoint for status."
        )

    # Run the check in the background without blocking
    asyncio.create_task(check_data_availability())


# Register all endpoints
register_endpoints(app)

# Make app available for uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
