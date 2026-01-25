"""API utility functions."""

from pathlib import Path
from typing import Optional

from shapely.geometry import Point, Polygon

from map_poster_creator.data.core import find_download_shp, resolve_city
from map_poster_creator.data.getters import get_city_df


def find_shp_from_polygon(
    polygon: Polygon, city: Optional[str] = None, country: Optional[str] = None
) -> Path:
    """
    Find the SHP directory for a polygon by using its centroid or city name.

    This function attempts to automatically determine the appropriate SHP region
    for a given polygon. It first tries to use the provided city name, and if that
    fails, it finds the nearest city to the polygon's centroid.

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

    # Otherwise, try to find region from polygon centroid
    # Find a city near the centroid to use for SHP lookup
    centroid = polygon.centroid

    # Try to find the nearest city to the centroid
    try:
        city_df = get_city_df()
        centroid_point = Point(centroid.x, centroid.y)

        # Find cities within a reasonable distance (rough bounding box)
        # This is a simplified approach - in production you might want spatial indexing
        min_lon, min_lat, max_lon, max_lat = polygon.bounds
        # Expand bounds slightly
        margin = 0.1
        candidates = city_df[
            (city_df["longitude"] >= min_lon - margin)
            & (city_df["longitude"] <= max_lon + margin)
            & (city_df["latitude"] >= min_lat - margin)
            & (city_df["latitude"] <= max_lat + margin)
        ]

        if not candidates.empty:
            # Find the closest city
            candidates = candidates.copy()
            candidates["distance"] = candidates.apply(
                lambda row: centroid_point.distance(
                    Point(float(row["longitude"]), float(row["latitude"]))
                ),
                axis=1,
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
    from fastapi import HTTPException

    raise HTTPException(
        status_code=400,
        detail="Could not automatically determine SHP region. Please provide 'shp_path' or 'city' parameter.",
    )
