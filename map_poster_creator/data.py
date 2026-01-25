"""
Backward compatibility module.

This module re-exports functions from the refactored modules to maintain
backward compatibility with existing code.
"""

# Re-export getters
from map_poster_creator.data.getters import (
    get_city_df,
    get_country_df,
    get_regions_tree,
    get_geofabrik_urls,
    get_region_polygons,
    get_all_region_polygons,
    get_region_centroids,
    get_geoboundaries_gdf,
    get_cities_geonames,
)

# Re-export core functions
from map_poster_creator.data.core import (
    resolve_city,
    find_download_shp,
    get_geojson_path_from_geoboundaries,
    GEOJSON_URL,
    GEOFABRIK_URL,
    GEOFABRIK_HREF_ATTRIBUTE_END,
    is_valid_download_url,
    is_valid_a_tag,
)

# Re-export geometry functions
from map_poster_creator.geometry import (
    MapGeometry,
    is_point_in_polygon,
    read_coordinates_from_file,
    polygon_from_coordinates,
    create_geojson_from_points,
    get_polygon_from_geojson,
    get_map_geometry_from_poly,
)

__all__ = [
    # Getters
    "get_city_df",
    "get_country_df",
    "get_regions_tree",
    "get_geofabrik_urls",
    "get_region_polygons",
    "get_all_region_polygons",
    "get_region_centroids",
    "get_geoboundaries_gdf",
    "get_cities_geonames",
    # Core functions
    "resolve_city",
    "find_download_shp",
    "get_geojson_path_from_geoboundaries",
    "GEOJSON_URL",
    "GEOFABRIK_URL",
    "GEOFABRIK_HREF_ATTRIBUTE_END",
    "is_valid_download_url",
    "is_valid_a_tag",
    # Geometry functions
    "MapGeometry",
    "is_point_in_polygon",
    "read_coordinates_from_file",
    "polygon_from_coordinates",
    "create_geojson_from_points",
    "get_polygon_from_geojson",
    "get_map_geometry_from_poly",
]
