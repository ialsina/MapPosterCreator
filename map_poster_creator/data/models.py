from functools import cache
import json
import logging
import traceback
from typing import Mapping, Sequence

from pandas import DataFrame, read_csv
from ete3 import Tree
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point

from map_poster_creator.config import paths
from map_poster_creator.data.base import BaseModel

logger = logging.getLogger(__name__)


class CityDataFrame(BaseModel[DataFrame]):
    """Model for loading city data from GeoNames."""

    is_tiny_feature = False  # Requires full installation

    def fetch(self) -> DataFrame:
        if not paths.cities_geonames_1000.exists():
            raise FileNotFoundError(
                "Could not find city data. "
                "If running in a container, this feature may be unavailable."
            )
        return read_csv(
            paths.cities_geonames_1000, index_col=0, low_memory=False
        ).fillna("")


class CountryDataFrame(BaseModel[DataFrame]):
    """Model for loading country data."""

    is_tiny_feature = False  # Requires full installation

    def fetch(self) -> DataFrame:
        if not paths.countries.exists():
            raise FileNotFoundError(
                "Could not find country data. "
                "If running in a container, this feature may be unavailable."
            )
        return read_csv(paths.countries)


class RegionsTree(BaseModel[Tree]):
    """Model for loading the regions tree from GeoFabrik."""

    is_tiny_feature = True  # Available in tiny mode

    def fetch(self) -> Tree:
        if not paths.geofabrik_tree_nw.exists():
            raise FileNotFoundError(
                "Could not find region tree data. "
                "If running in a container, this feature may be unavailable."
            )
        try:
            tree = Tree(str(paths.geofabrik_tree_nw), format=1)
            logger.info(f"Successfully loaded regions tree from {paths.geofabrik_tree_nw}")
            return tree
        except Exception as e:
            error_msg = str(e)
            full_traceback = traceback.format_exc()
            logger.error(f"Error loading regions tree: {error_msg}")
            logger.error(f"Full traceback:\n{full_traceback}")
            raise FileNotFoundError(
                f"Could not parse region tree data file {paths.geofabrik_tree_nw}. "
                f"Error: {error_msg}. "
                f"Full traceback: {full_traceback}. "
                f"Please check that the file is a valid newick format file, "
                f"or regenerate it using build_region_tree.py"
            ) from e


class GeofabrikUrls(BaseModel[Mapping[str, str]]):
    """Model for loading GeoFabrik URLs mapping."""

    is_tiny_feature = True  # Available in tiny mode

    def fetch(self) -> Mapping[str, str]:
        if not paths.geofabrik_urls.exists():
            raise FileNotFoundError(
                "Could not find GeoFabrik URLs data. "
                "If running in a container, this feature may be unavailable."
            )
        with open(paths.geofabrik_urls, "r", encoding="utf-8") as rf:
            return json.load(rf)


class GeoboundariesGDF(BaseModel[GeoDataFrame]):
    """Model for loading geoboundaries GeoDataFrame."""

    is_tiny_feature = False  # Requires full installation

    def fetch(self) -> GeoDataFrame:
        if not paths.geoboundaries_path.exists():
            raise FileNotFoundError(
                "Could not find geoboundaries data. "
                "If running in a container, this feature may be unavailable."
            )
        gdf = GeoDataFrame.from_file(paths.geoboundaries_path)
        gdf = gdf.to_crs("EPSG:4326")
        return gdf


class CitiesGeonames(BaseModel[DataFrame]):
    """Model for loading cities GeoNames DataFrame."""

    is_tiny_feature = False  # Requires full installation

    def fetch(self) -> DataFrame:
        if not paths.cities_geonames_1000.exists():
            raise FileNotFoundError(
                "Could not find city data. "
                "If running in a container, this feature may be unavailable."
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
        # Only leaf nodes should have polygon features
        # Accessing features on non-leaf nodes might trigger parsing errors
        if not node.is_leaf():
            return []
        try:
            # Safely check if polygon feature exists
            # Accessing node.features might trigger NHX parsing, so catch errors
            if "polygon" not in node.features:
                return []
        except Exception as e:
            # If accessing features fails (e.g., newick parsing error), return empty
            logger.debug(f"Error accessing features for node '{node.name if hasattr(node, 'name') else 'unknown'}': {e}")
            return []
        try:
            return self._parse_polygons(node.polygon)
        except ValueError:
            return []
        except Exception as e:
            # Catch any other errors when accessing polygon (e.g., newick format issues)
            logger.debug(f"Error parsing polygon for node '{node.name if hasattr(node, 'name') else 'unknown'}': {e}")
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

    def _get_all_region_polygons_impl(
        self, only_leaf: bool
    ) -> Mapping[Tree, Sequence[Polygon]]:
        """Internal implementation for getting all region polygons."""
        polygons = {}
        try:
            tree_iter = self._regions_tree.data.traverse()
            if tree_iter is None:
                return {}
            for node in tree_iter:
                # Skip non-leaf nodes when only_leaf is True
                if only_leaf and not node.is_leaf():
                    continue
                # Additional safety: only process leaf nodes for polygon access
                # Non-leaf nodes might cause newick parsing errors when accessing features
                # Even if only_leaf=False, we skip non-leaf nodes for polygon access
                # since only leaf nodes should have polygon features
                if not node.is_leaf():
                    continue
                polygons[node] = self._region_polygons_model.get(node)
        except Exception as e:
            error_msg = str(e)
            full_traceback = traceback.format_exc()
            logger.error(f"Error traversing regions tree: {error_msg}")
            logger.error(f"Full traceback:\n{full_traceback}")
            # Re-raise with more context
            raise RuntimeError(
                f"Error traversing regions tree: {error_msg}. "
                f"This may indicate an issue with the newick tree file format. "
                f"Full traceback: {full_traceback}"
            ) from e
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

    def _get_region_centroids_impl(
        self, only_leaf: bool
    ) -> Mapping[Tree, Sequence[Point]]:
        """Internal implementation for getting region centroids."""
        polygons = self._all_region_polygons_model.get(only_leaf)
        centroids = {}
        for node, polygon_lst in polygons.items():
            centroids[node] = [polygon.centroid for polygon in polygon_lst]
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
