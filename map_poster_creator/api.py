"""
FastAPI application for creating map posters from polygon coordinates.
"""
import io
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from shapely.geometry import Point, Polygon

from .colorscheme import ColorScheme, get_colorscheme, get_colorschemes
from .config import config, paths
from .core import create_poster_from_coordinates
from .data import (
    find_download_shp,
    polygon_from_coordinates,
    resolve_city,
    get_region_centroids,
    get_region_polygons,
    get_regions_tree,
    is_point_in_polygon,
)

app = FastAPI(
    title="Map Poster Creator API",
    description="API for creating map posters from polygon coordinates",
    version="0.8.0",
)


class Coordinate(BaseModel):
    """A single coordinate point (longitude, latitude)."""
    lon: float = Field(..., description="Longitude", ge=-180, le=180)
    lat: float = Field(..., description="Latitude", ge=-90, le=90)


class PosterRequest(BaseModel):
    """Request model for creating a poster."""
    coordinates: List[Coordinate] = Field(
        ...,
        min_length=3,
        description="List of coordinates defining the polygon boundary (minimum 3 points)"
    )
    shp_path: Optional[str] = Field(
        None,
        description=(
            "Path to SHP directory containing OpenStreetMap data (roads, water, greens). "
            "If not provided, will attempt to automatically find and download the appropriate "
            "regional dataset based on the polygon location or city name. "
            "SHP files contain the map features (roads, rivers, parks) that get rendered inside your polygon boundary."
        )
    )
    city: Optional[str] = Field(
        None,
        description=(
            "City name to help automatically find the correct regional SHP dataset. "
            "This makes auto-detection more reliable."
        )
    )
    country: Optional[str] = Field(
        None,
        description=(
            "Country name to help automatically find the correct regional SHP dataset. "
            "Use with 'city' for better accuracy."
        )
    )
    color: str = Field(
        "white",
        description="Color scheme name. Use /colors endpoint to see available schemes."
    )
    width: float = Field(
        15.0,
        description="Width of the poster in inches",
        gt=0
    )
    dpi: int = Field(
        300,
        description="Dots per inch (resolution)",
        gt=0,
        le=600
    )

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v: List[Coordinate]) -> List[Coordinate]:
        if len(v) < 3:
            raise ValueError("At least 3 coordinates are required to define a polygon")
        return v


def _find_shp_from_polygon(polygon: Polygon, city: Optional[str] = None, country: Optional[str] = None) -> Path:
    """
    Find the SHP directory for a polygon by using its centroid or city name.
    
    Args:
        polygon: The polygon to find SHP for
        city: Optional city name to help locate the region
        country: Optional country name to help locate the region
    
    Returns:
        Path to the SHP directory
    """
    # If city is provided, use it to find SHP
    if city:
        try:
            city_series = resolve_city(city=city, country=country, interactive=False, first=True)
            if city_series is not None:
                return find_download_shp(
                    city=city,
                    country=country,
                    interactive=False,
                    calculate_point=True,
                )
        except (ValueError, NotImplementedError):
            pass
    
    # Otherwise, try to find region from polygon centroid
    # Find a city near the centroid to use for SHP lookup
    centroid = polygon.centroid
    
    # Try to find the nearest city to the centroid
    from .data import get_city_df
    try:
        city_df = get_city_df()
        centroid_point = Point(centroid.x, centroid.y)
        
        # Find cities within a reasonable distance (rough bounding box)
        # This is a simplified approach - in production you might want spatial indexing
        min_lon, min_lat, max_lon, max_lat = polygon.bounds
        # Expand bounds slightly
        margin = 0.1
        candidates = city_df[
            (city_df["longitude"] >= min_lon - margin) &
            (city_df["longitude"] <= max_lon + margin) &
            (city_df["latitude"] >= min_lat - margin) &
            (city_df["latitude"] <= max_lat + margin)
        ]
        
        if not candidates.empty:
            # Find the closest city
            candidates = candidates.copy()
            candidates["distance"] = candidates.apply(
                lambda row: centroid_point.distance(
                    Point(float(row["longitude"]), float(row["latitude"]))
                ),
                axis=1
            )
            closest_city = candidates.nsmallest(1, "distance").iloc[0]
            
            # Try to find SHP using this city
            try:
                return find_download_shp(
                    city=closest_city["name"],
                    country=None,
                    interactive=False,
                    calculate_point=True,
                )
            except (ValueError, NotImplementedError):
                pass
    except Exception:
        pass
    
    # If all else fails, raise an error
    raise HTTPException(
        status_code=400,
        detail="Could not automatically determine SHP region. Please provide 'shp_path' or 'city' parameter."
    )


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
            "/health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


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
        }
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
                    detail=f"SHP directory not found: {request.shp_path}"
                )
        else:
            # Try to find SHP automatically
            try:
                shp_dir = _find_shp_from_polygon(polygon, request.city, request.country)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not automatically determine SHP region: {str(e)}. Please provide 'shp_path' or 'city' parameter."
                )
        
        # Get color scheme
        try:
            color_scheme = get_colorscheme(request.color)
        except KeyError:
            available = list(get_colorschemes().keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown color scheme '{request.color}'. Available schemes: {', '.join(available)}"
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
                status_code=500,
                detail=f"Error creating poster: {str(e)}"
            )
        
        # Return the image file
        if not output_file.exists():
            raise HTTPException(
                status_code=500,
                detail="Poster file was not created"
            )
        
        return FileResponse(
            path=output_file,
            media_type="image/png",
            filename=f"poster_{request.color}.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


class PosterRequestSimple(BaseModel):
    """Simplified request model that accepts coordinates as a list of lists."""
    coordinates: List[List[float]] = Field(
        ...,
        min_length=3,
        description="List of [lon, lat] coordinate pairs: [[lon1, lat1], [lon2, lat2], ...]"
    )
    shp_path: Optional[str] = Field(
        None,
        description="Path to SHP directory. If not provided, will attempt to find automatically."
    )
    city: Optional[str] = Field(
        None,
        description="City name to help find the SHP region automatically"
    )
    country: Optional[str] = Field(
        None,
        description="Country name to help find the SHP region automatically"
    )
    color: str = Field(
        "white",
        description="Color scheme name. Use /colors endpoint to see available schemes."
    )
    width: float = Field(
        15.0,
        description="Width of the poster in inches",
        gt=0
    )
    dpi: int = Field(
        300,
        description="Dots per inch (resolution)",
        gt=0,
        le=600
    )

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) < 3:
            raise ValueError("At least 3 coordinates are required to define a polygon")
        for coord in v:
            if not isinstance(coord, list) or len(coord) < 2:
                raise ValueError("Each coordinate must be a list with at least 2 elements [lon, lat]")
        return v


@app.post("/poster/simple")
async def create_poster_simple(request: PosterRequestSimple):
    """
    Alternative endpoint that accepts coordinates as a simple JSON array in the request body.
    
    Coordinates should be provided as: [[lon1, lat1], [lon2, lat2], ...]
    This is a simpler format than the main /poster endpoint.
    """
    # Convert to Coordinate objects
    try:
        coord_objects = [Coordinate(lon=c[0], lat=c[1]) for c in request.coordinates]
    except (IndexError, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid coordinate format. Expected [[lon, lat], ...]. Error: {str(e)}"
        )
    
    # Create PosterRequest from the simple request
    poster_request = PosterRequest(
        coordinates=coord_objects,
        shp_path=request.shp_path,
        city=request.city,
        country=request.country,
        color=request.color,
        width=request.width,
        dpi=request.dpi,
    )
    
    return await create_poster_endpoint(poster_request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

