"""Data models package."""

# Import getters
# Import constants from config
from map_poster_creator.config import (
    GEOFABRIK_HREF_ATTRIBUTE_END,
    GEOFABRIK_URL,
    GEOJSON_URL,
)

# Import core functions
from map_poster_creator.data.core import (
    find_download_shp,
    find_download_shp_from_point,
    get_geojson_path_from_geoboundaries,
    resolve_city,
)
from map_poster_creator.data.getters import (
    get_all_region_polygons,
    get_cities_geonames,
    get_city_df,
    get_country_df,
    get_geoboundaries_gdf,
    get_geofabrik_urls,
    get_region_centroids,
    get_region_polygons,
    get_regions_tree,
)

# Import interactive functions from data.interactive (no circular import)
from map_poster_creator.data.interactive import (
    browser_get_geojson_path_interactive,
    download_shp_interactive,
    interactive_region_choose,
    interactive_resolve_city,
)

# Import utility functions from data.utils
from map_poster_creator.data.utils import (
    _ask_reuse,
    _download_extract_shp,
    _exit_if_empty_file,
    _find_shp_url,
    _open_text_editor,
    _remove_hash_trailing_lines,
    is_valid_a_tag,
    is_valid_download_url,
)

# Import geometry functions directly (no circular import since geometry.py
# no longer imports from data)
from map_poster_creator.geometry import (
    MapGeometry,
    create_geojson_from_points,
    get_map_geometry_from_poly,
    get_polygon_from_geojson,
    is_point_in_polygon,
    polygon_from_coordinates,
    read_coordinates_from_file,
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
    # Constants (from config)
    "GEOJSON_URL",
    "GEOFABRIK_URL",
    "GEOFABRIK_HREF_ATTRIBUTE_END",
    # Utility functions (from data.utils)
    "_open_text_editor",
    "_remove_hash_trailing_lines",
    "_ask_reuse",
    "_exit_if_empty_file",
    "_find_shp_url",
    "_download_extract_shp",
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
    # Interactive functions
    "download_shp_interactive",
    "interactive_resolve_city",
    "browser_get_geojson_path_interactive",
    "interactive_region_choose",
]
