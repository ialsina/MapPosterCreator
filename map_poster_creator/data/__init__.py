"""Data models package."""

# Import getters
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

# Import core functions (including private utility functions)
from map_poster_creator.data.core import (
    resolve_city,
    find_download_shp,
    find_download_shp_from_point,
    get_geojson_path_from_geoboundaries,
    GEOJSON_URL,
    GEOFABRIK_URL,
    GEOFABRIK_HREF_ATTRIBUTE_END,
    is_valid_download_url,
    is_valid_a_tag,
    # Private utility functions
    _open_text_editor,
    _remove_hash_trailing_lines,
    _ask_reuse,
    _exit_if_empty_file,
    _find_shp_url,
    _download_extract_shp,
)

# Import geometry functions directly (no circular import since geometry.py no longer imports from data)
from map_poster_creator.geometry import (
    MapGeometry,
    is_point_in_polygon,
    read_coordinates_from_file,
    polygon_from_coordinates,
    create_geojson_from_points,
    get_polygon_from_geojson,
    get_map_geometry_from_poly,
)

# Import interactive functions from data.interactive (no circular import)
from map_poster_creator.data.interactive import (
    download_shp_interactive,
    interactive_resolve_city,
    browser_get_geojson_path_interactive,
    interactive_region_choose,
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
    "find_download_shp_from_point",
    "get_geojson_path_from_geoboundaries",
    "GEOJSON_URL",
    "GEOFABRIK_URL",
    "GEOFABRIK_HREF_ATTRIBUTE_END",
    "is_valid_download_url",
    "is_valid_a_tag",
    # Private utility functions
    "_open_text_editor",
    "_remove_hash_trailing_lines",
    "_ask_reuse",
    "_exit_if_empty_file",
    "_find_shp_url",
    "_download_extract_shp",
    # Geometry functions
    "MapGeometry",
    "is_point_in_polygon",
    "read_coordinates_from_file",
    "polygon_from_coordinates",
    "create_geojson_from_points",
    "get_polygon_from_geojson",
    "get_map_geometry_from_poly",
    # Interactive functions
    "download_shp_interactive",
    "interactive_resolve_city",
    "browser_get_geojson_path_interactive",
    "interactive_region_choose",
]
