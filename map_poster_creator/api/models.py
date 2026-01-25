"""Pydantic models for API requests and responses."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Coordinate(BaseModel):
    """A single coordinate point (longitude, latitude)."""

    lon: float = Field(..., description="Longitude", ge=-180, le=180)
    lat: float = Field(..., description="Latitude", ge=-90, le=90)


class PosterRequest(BaseModel):
    """Request model for creating a poster."""

    coordinates: List[Coordinate] = Field(
        ...,
        min_length=3,
        description="List of coordinates defining the polygon boundary (minimum 3 points)",
    )
    shp_path: Optional[str] = Field(
        None,
        description=(
            "Path to SHP directory containing OpenStreetMap data (roads, water, greens). "
            "If not provided, will attempt to automatically find and download the appropriate "
            "regional dataset based on the polygon location or city name. "
            "SHP files contain the map features (roads, rivers, parks) that get rendered inside your polygon boundary."
        ),
    )
    city: Optional[str] = Field(
        None,
        description=(
            "City name to help automatically find the correct regional SHP dataset. "
            "This makes auto-detection more reliable."
        ),
    )
    country: Optional[str] = Field(
        None,
        description=(
            "Country name to help automatically find the correct regional SHP dataset. "
            "Use with 'city' for better accuracy."
        ),
    )
    color: str = Field(
        "white",
        description="Color scheme name. Use /colors endpoint to see available schemes.",
    )
    width: float = Field(15.0, description="Width of the poster in inches", gt=0)
    dpi: int = Field(300, description="Dots per inch (resolution)", gt=0, le=600)

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[Coordinate]) -> List[Coordinate]:
        if len(v) < 3:
            raise ValueError("At least 3 coordinates are required to define a polygon")
        return v


class PosterRequestSimple(BaseModel):
    """Simplified request model that accepts coordinates as a list of lists."""

    coordinates: List[List[float]] = Field(
        ...,
        min_length=3,
        description="List of [lon, lat] coordinate pairs: [[lon1, lat1], [lon2, lat2], ...]",
    )
    shp_path: Optional[str] = Field(
        None,
        description="Path to SHP directory. If not provided, will attempt to find automatically.",
    )
    city: Optional[str] = Field(
        None, description="City name to help find the SHP region automatically"
    )
    country: Optional[str] = Field(
        None, description="Country name to help find the SHP region automatically"
    )
    color: str = Field(
        "white",
        description="Color scheme name. Use /colors endpoint to see available schemes.",
    )
    width: float = Field(15.0, description="Width of the poster in inches", gt=0)
    dpi: int = Field(300, description="Dots per inch (resolution)", gt=0, le=600)

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) < 3:
            raise ValueError("At least 3 coordinates are required to define a polygon")
        for coord in v:
            if not isinstance(coord, list) or len(coord) < 2:
                raise ValueError(
                    "Each coordinate must be a list with at least 2 elements [lon, lat]"
                )
        return v
