from functools import cache
from pathlib import Path
import json
from typing import Mapping, Sequence

from pandas import DataFrame, read_csv
from ete3 import Tree
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point

from map_poster_creator.config import paths
from map_poster_creator.data.base import CachedModel


class CityDataFrame(CachedModel[DataFrame]):
    """Model for loading city data from GeoNames."""
    
    def fetch(self) -> DataFrame:
        if not paths.cities_geonames_1000.exists():
            raise FileNotFoundError(
                "Could not find city data. Please download using the appropriate script."
            )
        return read_csv(
            paths.cities_geonames_1000,
            index_col=0,
            low_memory=False
        ).fillna("")


class CountryDataFrame(CachedModel[DataFrame]):
    """Model for loading country data."""
    
    def fetch(self) -> DataFrame:
        if not paths.countries.exists():
            raise FileNotFoundError(
                "Could not find country data. Please download using the appropriate script."
            )
        return read_csv(paths.countries)


class RegionsTree(CachedModel[Tree]):
    """Model for loading the regions tree from GeoFabrik."""
    
    def fetch(self) -> Tree:
        return Tree(str(paths.geofabrik_tree_nw), format=1)


class GeofabrikUrls(CachedModel[Mapping[str, str]]):
    """Model for loading GeoFabrik URLs mapping."""
    
    def fetch(self) -> Mapping[str, str]:
        with open(paths.geofabrik_urls, "r", encoding="utf-8") as rf:
            return json.load(rf)


class GeoboundariesGDF(CachedModel[GeoDataFrame]):
    """Model for loading geoboundaries GeoDataFrame."""
    
    def fetch(self) -> GeoDataFrame:
        if not paths.geoboundaries_path.exists():
            raise FileNotFoundError(
                "Could not find geoboundaries data. Please ensure geoBoundariesCGAZ_ADM2.geojson exists."
            )
        gdf = GeoDataFrame.from_file(paths.geoboundaries_path)
        gdf = gdf.to_crs("EPSG:4326")
        return gdf


class CitiesGeonames(CachedModel[DataFrame]):
    """Model for loading cities GeoNames DataFrame."""
    
    def fetch(self) -> DataFrame:
        if not paths.cities_geonames_1000.exists():
            raise FileNotFoundError(
                "Could not find city data. Please download using the appropriate script."
            )
        return read_csv(paths.cities_geonames_1000, index_col=0, low_memory=False)


class RegionPolygonsModel:
    """
    Model for getting region polygons for a specific node.
    This uses cache internally to cache results per node.
    """
    
    def __init__(self):
        self._cached_get = cache(self._get_region_polygons_impl)
    
    def _parse_polygons(self, data: str) -> Sequence[Polygon]:
        """Parse polygon data from string format."""
        polygons = []
        current_polygon = []

        for line in data.strip().split("_"):
            line = line.strip()
            if line == "END":
                if current_polygon:
                    polygons.append(Polygon(current_polygon))
                current_polygon = []
            elif line.replace("-", "").isalpha():
                continue
            elif line.isdigit():
                continue
            else:
                coords = list(map(float, line.split()))
                current_polygon.append(coords)
        return polygons
    
    def _get_region_polygons_impl(self, node: Tree) -> Sequence[Polygon]:
        """Internal implementation for getting region polygons."""
        if "polygon" not in node.features:
            return []
        try:
            return self._parse_polygons(node.polygon)
        except ValueError:
            return []
    
    def get(self, node: Tree) -> Sequence[Polygon]:
        """Get region polygons for a node."""
        return self._cached_get(node)


class AllRegionPolygonsModel:
    """
    Model for getting all region polygons.
    This uses cache internally to cache results per only_leaf parameter.
    """
    
    def __init__(self):
        self._cached_get = cache(self._get_all_region_polygons_impl)
        self._region_polygons_model = RegionPolygonsModel()
        self._regions_tree = RegionsTree()
    
    def _get_all_region_polygons_impl(self, only_leaf: bool) -> Mapping[Tree, Sequence[Polygon]]:
        """Internal implementation for getting all region polygons."""
        polygons = {}
        tree_iter = self._regions_tree.data.traverse()
        if tree_iter is None:
            return {}
        for node in tree_iter:
            if only_leaf and not node.is_leaf():
                continue
            polygons[node] = self._region_polygons_model.get(node)
        return polygons
    
    def get(self, only_leaf: bool = False) -> Mapping[Tree, Sequence[Polygon]]:
        """Get all region polygons, optionally only for leaf nodes."""
        return self._cached_get(only_leaf)


class RegionCentroidsModel:
    """
    Model for getting region centroids.
    This uses cache internally to cache results per only_leaf parameter.
    """
    
    def __init__(self):
        self._cached_get = cache(self._get_region_centroids_impl)
        self._all_region_polygons_model = AllRegionPolygonsModel()
    
    def _get_region_centroids_impl(self, only_leaf: bool) -> Mapping[Tree, Sequence[Point]]:
        """Internal implementation for getting region centroids."""
        polygons = self._all_region_polygons_model.get(only_leaf)
        centroids = {}
        for node, polygon_lst in polygons.items():
            centroids[node] = [
                polygon.centroid for polygon in polygon_lst
            ]
        return centroids
    
    def get(self, only_leaf: bool = False) -> Mapping[Tree, Sequence[Point]]:
        """Get all region centroids, optionally only for leaf nodes."""
        return self._cached_get(only_leaf)


# Singleton instances for easy access
_city_df = CityDataFrame()
_country_df = CountryDataFrame()
_regions_tree = RegionsTree()
_geofabrik_urls = GeofabrikUrls()
_geoboundaries_gdf = GeoboundariesGDF()
_cities_geonames = CitiesGeonames()
_region_polygons_model = RegionPolygonsModel()
_all_region_polygons_model = AllRegionPolygonsModel()
_region_centroids_model = RegionCentroidsModel()

