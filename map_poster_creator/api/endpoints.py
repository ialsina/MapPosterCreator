"""API endpoint handlers."""

import logging
import traceback
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import FileResponse

from map_poster_creator.colorscheme import get_colorscheme, get_colorschemes
from map_poster_creator.config import paths
from map_poster_creator.core import create_poster_from_coordinates
from map_poster_creator.data import polygon_from_coordinates
from map_poster_creator.api.models import Coordinate, PosterRequest, PosterRequestSimple
from map_poster_creator.api.utils import find_shp_from_polygon

logger = logging.getLogger(__name__)


def register_endpoints(app):
    """Register all API endpoints with the FastAPI app."""

    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Map Poster Creator API",
            "version": "0.8.0",
            "endpoints": {
                "/docs": "Interactive API documentation",
                "/poster": "Create a poster from coordinates (POST)",
                "/colors": "List available color schemes (GET)",
                "/health": "Health check endpoint",
            },
        }

    @app.get("/health")
    async def health():
        """
        Health check endpoint.

        Returns status and data availability information.
        """
        health_status = {"status": "healthy", "data_ready": False}

        try:
            # Check if critical data files are accessible
            from map_poster_creator.data.getters import get_regions_tree

            tree = get_regions_tree()
            node_count = len(list(tree.traverse()))
            health_status["data_ready"] = True
            health_status["regions_tree_nodes"] = node_count
        except Exception as e:
            # If data is not ready, still return 200 but indicate not ready
            # This allows the service to be "alive" but not fully operational
            health_status["status"] = "starting"
            health_status["message"] = "Data loading in progress"
            logger.debug(f"Health check: data not ready yet - {str(e)}")

        return health_status

    @app.get("/colors")
    async def list_colors():
        """List all available color schemes."""
        schemes = get_colorschemes()
        return {
            "available_colors": list(schemes.keys()),
            "schemes": {
                name: {
                    "facecolor": scheme.facecolor,
                    "water": scheme.water,
                    "greens": scheme.greens,
                    "roads": scheme.roads,
                }
                for name, scheme in schemes.items()
            },
        }

    @app.post("/poster")
    async def create_poster_endpoint(request: PosterRequest):
        """
        Create a map poster from a list of coordinates defining a polygon.

        The coordinates define the boundary of the area to display. The system will:
        1. Use your polygon coordinates to define the area boundary
        2. Automatically find/download the appropriate regional OpenStreetMap dataset (SHP files)
        3. Extract roads, water bodies, and green areas from the SHP data that fall within your polygon
        4. Render them as a beautiful map poster

        The coordinates should be provided as [longitude, latitude] pairs.
        The polygon will be automatically closed if the first and last points don't match.

        **Note**: SHP files contain the actual map features (roads, rivers, parks).
        The polygon coordinates only define which area to show. If auto-detection fails,
        you can provide 'shp_path' or 'city' to help locate the correct regional dataset.

        Returns the poster image as a PNG file.
        """
        try:
            # Convert coordinates to list of [lon, lat] pairs
            coords = [[coord.lon, coord.lat] for coord in request.coordinates]

            # Create polygon from coordinates
            polygon = polygon_from_coordinates(coords)

            # Determine SHP path
            if request.shp_path:
                shp_dir = Path(request.shp_path)
                if not shp_dir.exists():
                    raise HTTPException(
                        status_code=400,
                        detail=f"SHP directory not found: {request.shp_path}",
                    )
            else:
                # Try to find SHP automatically
                try:
                    shp_dir = find_shp_from_polygon(
                        polygon,
                        city=request.city,
                        country=request.country,
                        latitude=request.latitude,
                        longitude=request.longitude,
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    error_msg = str(e)
                    full_traceback = traceback.format_exc()
                    logger.error(f"Error finding SHP region: {error_msg}")
                    logger.debug(f"Full traceback:\n{full_traceback}")
                    # Return user-friendly error without traceback
                    raise HTTPException(
                        status_code=400,
                        detail="Could not automatically determine SHP region. Please provide 'shp_path' or 'city' parameter.",
                    )

            # Get color scheme
            try:
                color_scheme = get_colorscheme(request.color)
            except KeyError:
                available = list(get_colorschemes().keys())
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown color scheme '{request.color}'. Available schemes: {', '.join(available)}",
                )

            # Create temporary output file
            output_dir = paths.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"poster_{uuid4().hex[:8]}.png"

            # Create the poster
            try:
                create_poster_from_coordinates(
                    shp_dir=shp_dir,
                    coordinates=coords,
                    color=color_scheme,
                    width=request.width,
                    dpi=request.dpi,
                    output=output_file,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error creating poster: {str(e)}"
                )

            # Return the image file
            if not output_file.exists():
                raise HTTPException(
                    status_code=500, detail="Poster file was not created"
                )

            return FileResponse(
                path=output_file,
                media_type="image/png",
                filename=f"poster_{request.color}.png",
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @app.post("/poster/simple")
    async def create_poster_simple(request: PosterRequestSimple):
        """
        Alternative endpoint that accepts coordinates as a simple JSON array in the request body.

        Coordinates should be provided as: [[lon1, lat1], [lon2, lat2], ...]
        This is a simpler format than the main /poster endpoint.
        """
        # Convert to Coordinate objects
        try:
            coord_objects = [
                Coordinate(lon=c[0], lat=c[1]) for c in request.coordinates
            ]
        except (IndexError, ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid coordinate format. Expected [[lon, lat], ...]. Error: {str(e)}",
            )

        # Create PosterRequest from the simple request
        poster_request = PosterRequest(
            coordinates=coord_objects,
            shp_path=request.shp_path,
            city=request.city,
            country=request.country,
            latitude=request.latitude,
            longitude=request.longitude,
            color=request.color,
            width=request.width,
            dpi=request.dpi,
        )

        return await create_poster_endpoint(poster_request)
