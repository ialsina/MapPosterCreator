"""API utility functions."""

from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from shapely.geometry import Point, Polygon

from map_poster_creator.data.core import (
    find_download_shp,
    find_download_shp_from_point,
    resolve_city,
)


def find_shp_from_polygon(
    polygon: Polygon, city: Optional[str] = None, country: Optional[str] = None
) -> Path:
    """
    Find the SHP directory for a polygon by using its centroid or city name.

    This function attempts to automatically determine the appropriate SHP region
    for a given polygon. It first tries to use the provided city name, and if that
    fails, it uses the polygon's centroid directly to find the appropriate region.

    Args:
        polygon: The polygon to find SHP for
        city: Optional city name to help locate the region
        country: Optional country name to help locate the region

    Returns:
        Path to the SHP directory

    Raises:
        HTTPException: If SHP region cannot be determined
    """
    # If city is provided, use it to find SHP
    if city:
        try:
            city_series = resolve_city(
                city=city, country=country, interactive=False, first=True
            )
            if city_series is not None:
                return find_download_shp(
                    city=city,
                    country=country,
                    interactive=False,
                    calculate_point=True,
                )
        except (ValueError, NotImplementedError):
            pass

    # Otherwise, use polygon centroid directly to find region
    centroid = polygon.centroid
    centroid_point = Point(centroid.x, centroid.y)

    try:
        return find_download_shp_from_point(
            point=centroid_point,
            calculate_point=True,
            interactive=False,
            location_name="polygon centroid",
        )
    except (ValueError, NotImplementedError):
        pass

    # If all else fails, raise an error
    raise HTTPException(
        status_code=400,
        detail="Could not automatically determine SHP region. Please provide 'shp_path' or 'city' parameter.",
    )
