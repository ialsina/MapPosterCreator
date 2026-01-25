"""Getter functions for accessing data models."""

from typing import Mapping, Sequence
from ete3 import Tree
from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely.geometry import Point, Polygon

from map_poster_creator.data.models import (
    _city_df,
    _country_df,
    _regions_tree,
    _geofabrik_urls,
    _geoboundaries_gdf,
    _cities_geonames,
    _region_polygons_model,
    _all_region_polygons_model,
    _region_centroids_model,
)


def get_city_df() -> DataFrame:
    """Get city DataFrame from the model."""
    return _city_df.data


def get_country_df() -> DataFrame:
    """Get country DataFrame from the model."""
    return _country_df.data


def get_regions_tree() -> Tree:
    """Get regions tree from the model."""
    return _regions_tree.data


def get_geofabrik_urls() -> Mapping[str, str]:
    """Get GeoFabrik URLs from the model."""
    return _geofabrik_urls.data


def get_region_polygons(node: Tree) -> Sequence[Polygon]:
    """Get region polygons for a node from the model."""
    return _region_polygons_model.get(node)


def get_all_region_polygons(only_leaf: bool = False) -> Mapping[Tree, Sequence[Polygon]]:
    """Get all region polygons from the model."""
    return _all_region_polygons_model.get(only_leaf)


def get_region_centroids(only_leaf: bool = False) -> Mapping[Tree, Sequence[Point]]:
    """Get region centroids from the model."""
    return _region_centroids_model.get(only_leaf)


def get_geoboundaries_gdf() -> GeoDataFrame:
    """Get geoboundaries GeoDataFrame from the model."""
    return _geoboundaries_gdf.data


def get_cities_geonames() -> DataFrame:
    """Get cities GeoNames DataFrame from the model."""
    return _cities_geonames.data

