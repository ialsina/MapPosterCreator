"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field, field_validator


class Coordinate(BaseModel):
    """A single coordinate point (longitude, latitude)."""

    lon: float = Field(..., description="Longitude", ge=-180, le=180)
    lat: float = Field(..., description="Latitude", ge=-90, le=90)


class PosterRequest(BaseModel):
    """Request model for creating a poster."""

    coordinates: list[Coordinate] = Field(
        ...,
        min_length=3,
        description="List of coordinates defining the polygon boundary (minimum 3 points)",
    )
    shp_path: str | None = Field(
        None,
        description=(
            "Path to SHP directory containing OpenStreetMap data (roads, water, greens). "
            "If not provided, will attempt to automatically find and download the appropriate "
            "regional dataset based on the polygon location or city name. "
            "SHP files contain the map features (roads, rivers, parks) that get rendered inside your polygon boundary."
        ),
    )
    city: str | None = Field(
        None,
        description=(
            "City name to help automatically find the correct regional SHP dataset. "
            "This makes auto-detection more reliable."
        ),
    )
    country: str | None = Field(
        None,
        description=(
            "Country name to help automatically find the correct regional SHP dataset. "
            "Use with 'city' for better accuracy."
        ),
    )
    latitude: float | None = Field(
        None,
        ge=-90,
        le=90,
        description=(
            "Latitude coordinate to directly locate the SHP region. "
            "If provided along with longitude, this bypasses city/country lookup. "
            "Takes priority over city/country parameters."
        ),
    )
    longitude: float | None = Field(
        None,
        ge=-180,
        le=180,
        description=(
            "Longitude coordinate to directly locate the SHP region. "
            "If provided along with latitude, this bypasses city/country lookup. "
            "Takes priority over city/country parameters."
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
    def validate_coordinates(cls, v: list[Coordinate]) -> list[Coordinate]:
        if len(v) < 3:
            raise ValueError("At least 3 coordinates are required to define a polygon")
        return v


class PosterRequestSimple(BaseModel):
    """Simplified request model that accepts coordinates as a list of lists."""

    coordinates: list[list[float]] = Field(
        ...,
        min_length=3,
        description="List of [lon, lat] coordinate pairs: [[lon1, lat1], [lon2, lat2], ...]",
    )
    shp_path: str | None = Field(
        None,
        description="Path to SHP directory. If not provided, will attempt to find automatically.",
    )
    city: str | None = Field(
        None, description="City name to help find the SHP region automatically"
    )
    country: str | None = Field(
        None, description="Country name to help find the SHP region automatically"
    )
    latitude: float | None = Field(
        None,
        ge=-90,
        le=90,
        description=(
            "Latitude coordinate to directly locate the SHP region. "
            "If provided along with longitude, this bypasses city/country lookup. "
            "Takes priority over city/country parameters."
        ),
    )
    longitude: float | None = Field(
        None,
        ge=-180,
        le=180,
        description=(
            "Longitude coordinate to directly locate the SHP region. "
            "If provided along with latitude, this bypasses city/country lookup. "
            "Takes priority over city/country parameters."
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
    def validate_coordinates(cls, v: list[list[float]]) -> list[list[float]]:
        if len(v) < 3:
            raise ValueError("At least 3 coordinates are required to define a polygon")
        for coord in v:
            if not isinstance(coord, list) or len(coord) < 2:
                raise ValueError(
                    "Each coordinate must be a list with at least 2 elements [lon, lat]"
                )
        return v
