"""Data-dependent geometry functions.

This module contains geometry functions that depend on data access.
Pure geometry utilities are in map_poster_creator.geometry.
"""

from pandas import Series
from shapely.geometry import MultiPolygon, Point, Polygon

from map_poster_creator.data.getters import get_geoboundaries_gdf


def _get_city_point_from_series(city_series: Series) -> Point:
    """Get a Point geometry for a city from a resolved city Series."""
    lat = city_series["latitude"]
    lon = city_series["longitude"]
    return Point(lon, lat)


def _get_city_polygon_from_geoboundaries(city_series: Series) -> Polygon | MultiPolygon:
    """Get the administrative boundary polygon for a city from geoboundaries."""
    pt = _get_city_point_from_series(city_series)
    gdf = get_geoboundaries_gdf()

    # Use spatial index to get possible matches
    possible_matches_index = list(gdf.sindex.intersection(pt.bounds))
    if not possible_matches_index:
        city_name = city_series.get("name", "unknown")
        country_code = city_series.get("country code", "unknown")
        raise ValueError(
            f'No geoboundaries found near city "{city_name}" with country code "{country_code}".'
        )
    possible_matches = gdf.iloc[possible_matches_index]

    # Filter precisely
    city_poly = possible_matches[possible_matches.contains(pt)]

    if city_poly.empty:
        city_name = city_series.get("name", "unknown")
        country_code = city_series.get("country code", "unknown")
        raise ValueError(
            f'No polygon found containing city "{city_name}" with country code "{country_code}".'
        )

    # Return the first matching polygon's geometry (could be Polygon or MultiPolygon)
    return city_poly.iloc[0].geometry
