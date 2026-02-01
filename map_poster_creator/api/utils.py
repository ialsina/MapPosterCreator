"""API utility functions."""

import logging
import traceback
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from shapely.geometry import Point, Polygon

from map_poster_creator.data.core import (
    find_download_shp,
    find_download_shp_from_point,
    resolve_city,
)

logger = logging.getLogger(__name__)


def find_shp_from_latitude_longitude(
    latitude: float, longitude: float
) -> Path:
    """
    Find the SHP directory for a latitude and longitude.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Path to the SHP directory

    Raises:
        HTTPException: If SHP region cannot be determined
    """
    # Create a Point from the lat/lon coordinates
    # Note: Point uses (x, y) which corresponds to (lon, lat)
    point = Point(longitude, latitude)

    try:
        return find_download_shp_from_point(
            point=point,
            calculate_point=True,
            interactive=False,
            location_name=f"point ({latitude}, {longitude})",
        )
    except (ValueError, NotImplementedError) as e:
        error_msg = str(e)
        full_traceback = traceback.format_exc()
        logger.error(f"Error finding SHP from lat/lon ({latitude}, {longitude}): {error_msg}")
        logger.debug(f"Full traceback:\n{full_traceback}")
        # Return user-friendly error without traceback
        raise HTTPException(
            status_code=400,
            detail=f"Could not automatically determine SHP region from coordinates ({latitude}, {longitude}). Please provide 'shp_path' or 'city' parameter.",
        )
    except Exception as e:
        error_msg = str(e)
        full_traceback = traceback.format_exc()
        logger.error(f"Unexpected error finding SHP from lat/lon ({latitude}, {longitude}): {error_msg}")
        logger.debug(f"Full traceback:\n{full_traceback}")
        # Check if it's a newick format error
        if "newick format" in error_msg.lower() or ":1" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="Error loading region data. Please contact support or try again later.",
            )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while finding the region. Please try again or provide 'shp_path' parameter.",
        )


def find_shp_from_polygon(
    polygon: Polygon,
    city: Optional[str] = None,
    country: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Path:
    """
    Find the SHP directory for a polygon by using lat/lon, city name, or centroid.

    This function attempts to automatically determine the appropriate SHP region
    for a given polygon. It prioritizes:
    1. Explicit lat/lon coordinates (if provided)
    2. City name (if provided)
    3. Polygon centroid (as fallback)

    Args:
        polygon: The polygon to find SHP for
        city: Optional city name to help locate the region
        country: Optional country name to help locate the region
        latitude: Optional latitude coordinate to directly locate the region
        longitude: Optional longitude coordinate to directly locate the region

    Returns:
        Path to the SHP directory

    Raises:
        HTTPException: If SHP region cannot be determined
    """
    # If lat/lon are provided, use them directly (highest priority)
    if latitude is not None and longitude is not None:
        try:
            return find_shp_from_latitude_longitude(latitude, longitude)
        except HTTPException:
            raise
        except Exception as e:
            # If lat/lon lookup fails, fall through to other methods
            pass

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
        except ValueError as e:
            # If country lookup fails, provide more specific error and don't fall back
            error_msg = str(e)
            if "Country" in error_msg and "not found" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail=f"{error_msg} Please provide a valid country name or use 'shp_path' parameter.",
                )
            # For other ValueErrors (like no regions found), fall through to centroid method
            pass
        except NotImplementedError:
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
    except (ValueError, NotImplementedError) as e:
        error_msg = str(e)
        full_traceback = traceback.format_exc()
        logger.error(f"Error finding SHP from polygon centroid: {error_msg}")
        logger.debug(f"Full traceback:\n{full_traceback}")
        # Fall through to final error
        pass
    except Exception as e:
        error_msg = str(e)
        full_traceback = traceback.format_exc()
        logger.error(f"Unexpected error finding SHP from polygon centroid: {error_msg}")
        logger.debug(f"Full traceback:\n{full_traceback}")
        # Check if it's a newick format error
        if "newick format" in error_msg.lower() or ":1" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="Error loading region data. Please contact support or try again later.",
            )
        # Fall through to final error
        pass

    # If all else fails, raise an error
    raise HTTPException(
        status_code=400,
        detail="Could not automatically determine SHP region. Please provide 'shp_path' or 'city' parameter.",
    )
