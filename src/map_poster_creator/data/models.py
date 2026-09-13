from functools import cache
import json
import logging
import time
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

        # Check file is readable and has content (might be still copying)
        try:
            file_size = paths.geofabrik_tree_nw.stat().st_size
            if file_size == 0:
                raise FileNotFoundError(
                    f"Region tree file {paths.geofabrik_tree_nw} exists but is empty. "
                    "The file may still be copying."
                )
        except OSError as e:
            raise FileNotFoundError(
                f"Cannot access region tree file {paths.geofabrik_tree_nw}: {e}"
            ) from e

        # Retry logic for robustness (handles cases where file might not be fully ready)
        # Using format=1 as specified (NHX format with internal node names)
        # Read file into memory first to avoid file handle/buffering issues
        max_retries = 5  # Increased from 3
        retry_delay = 1.0  # Increased initial delay from 0.5s

        last_error = None
        last_content_size = 0

        for attempt in range(max_retries):
            try:
                # Read the entire file into memory first, then parse from string
                # This avoids potential file handle/buffering issues that might cause
                # partial reads or parsing errors
                # Try different encodings if utf-8 fails
                newick_content = None
                for encoding in ["utf-8", "latin-1", "ascii"]:
                    try:
                        with open(paths.geofabrik_tree_nw, "r", encoding=encoding) as f:
                            newick_content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue

                if newick_content is None:
                    raise FileNotFoundError(f"Could not read file with any encoding")

                # Validate we have content
                if not newick_content or not newick_content.strip():
                    raise FileNotFoundError(
                        f"File is empty or contains only whitespace"
                    )

                # Check if content looks suspiciously small (might be partial copy)
                content_size = len(newick_content)
                last_content_size = content_size
                if content_size < 50:  # A valid newick tree should be at least 50 chars
                    raise ValueError(
                        f"File appears incomplete (only {content_size} chars). "
                        f"Possibly still being copied."
                    )

                # Parse from string instead of file path
                # This ensures we have the complete file content before parsing
                tree = Tree(newick_content, format=1)

                # Validate the tree has nodes
                node_count = len(list(tree.traverse()))
                if node_count == 0:
                    raise ValueError("Parsed tree has no nodes")

                logger.info(
                    f"Successfully loaded regions tree from {paths.geofabrik_tree_nw} "
                    f"(attempt {attempt + 1}, size: {content_size} chars, nodes: {node_count})"
                )
                return tree
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.debug(
                    f"Failed to load tree (attempt {attempt + 1}/{max_retries}): {error_msg}"
                )

                # If we have retries left, wait and try again
                if attempt < max_retries - 1:
                    logger.debug(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Last attempt failed, break and raise
                    break

        # If all retries failed, log and raise
        error_msg = str(last_error) if last_error else "Unknown error"
        full_traceback = traceback.format_exc()
        logger.error(
            f"Error loading regions tree after {max_retries} attempts: {error_msg} "
            f"(last file size: {last_content_size} chars)"
        )
        logger.debug(f"Full traceback:\n{full_traceback}")
        # Raise error without traceback in message (traceback is in logs)
        raise FileNotFoundError(
            f"Could not parse region tree data file {paths.geofabrik_tree_nw}. "
            f"Error: {error_msg}. "
            f"Please check that the file is a valid newick format file, "
            f"or regenerate it using build_region_tree.py"
        ) from last_error


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
            logger.debug(
                f"Error accessing features for node '{node.name if hasattr(node, 'name') else 'unknown'}': {e}"
            )
            return []
        try:
            return self._parse_polygons(node.polygon)
        except ValueError:
            return []
        except Exception as e:
            # Catch any other errors when accessing polygon (e.g., newick format issues)
            logger.debug(
                f"Error parsing polygon for node '{node.name if hasattr(node, 'name') else 'unknown'}': {e}"
            )
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
        # Use the singleton instance to avoid multiple tree loads and potential conflicts
        # Access it lazily to avoid circular import issues
        self._regions_tree_singleton = None

    def _get_all_region_polygons_impl(
        self, only_leaf: bool
    ) -> Mapping[Tree, Sequence[Polygon]]:
        """Internal implementation for getting all region polygons."""
        polygons = {}
        try:
            # Use the singleton tree instance via getter to avoid multiple instances
            # This ensures we use the same tree instance that might already be loaded
            from map_poster_creator.data.getters import get_regions_tree

            tree = get_regions_tree()
            tree_iter = tree.traverse()
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
            logger.debug(f"Full traceback:\n{full_traceback}")
            # Re-raise with more context (without traceback in message)
            raise RuntimeError(
                f"Error traversing regions tree: {error_msg}. "
                f"This may indicate an issue with the newick tree file format."
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
