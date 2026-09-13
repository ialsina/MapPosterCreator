"""Geometry and GeoJSON utilities."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from geopandas import GeoDataFrame
from shapely.geometry import Point, Polygon, MultiPolygon

from map_poster_creator.config import paths

logger = logging.getLogger(__name__)


@dataclass
class MapGeometry:
    top: float
    bottom: float
    left: float
    right: float
    center: List[float]


def _parse_polygons(data: str) -> Sequence[Polygon]:
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


def is_point_in_polygon(point: Point, polygon: Polygon) -> bool:
    """Check if a point is inside a polygon."""
    polygon_gdf = GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])
    point_gdf = GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[point])
    return bool(polygon_gdf.contains(point_gdf.loc[0, "geometry"])[0])


def _polygon_to_geojson_file(geometry: Polygon | MultiPolygon, filepath: Path) -> None:
    """Save a Polygon or MultiPolygon to a GeoJSON file."""

    def convert_coord(coord):
        """Convert a coordinate to [lon, lat] format."""
        try:
            # Try to convert to tuple/list first if it's a numpy array or similar
            if hasattr(coord, "tolist"):
                coord = coord.tolist()
            # Handle tuple, list, or any sequence
            if hasattr(coord, "__getitem__") and hasattr(coord, "__len__"):
                if len(coord) >= 2:
                    return [float(coord[0]), float(coord[1])]
            # If it's already a float or single value, that's an error
            raise ValueError(
                f"Unexpected coordinate format: {coord} (type: {type(coord)})"
            )
        except (TypeError, IndexError, ValueError) as e:
            raise ValueError(f"Error converting coordinate {coord}: {e}") from e

    if isinstance(geometry, MultiPolygon):
        # MultiPolygon: convert each polygon's exterior coordinates
        coordinates = []
        for poly in geometry.geoms:
            poly_coords = [convert_coord(coord) for coord in poly.exterior.coords]
            coordinates.append(poly_coords)
        geometry_type = "MultiPolygon"
    else:
        # Polygon: convert exterior coordinates
        coordinates = [convert_coord(coord) for coord in geometry.exterior.coords]
        coordinates = [coordinates]  # Wrap in array for Polygon format
        geometry_type = "Polygon"

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": geometry_type, "coordinates": coordinates},
                "properties": {},
            }
        ],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(geojson, f)


def read_coordinates_from_file(file_path: Path | str) -> Sequence[Sequence[float]]:
    """
    Read coordinates from a file.

    The file can be in one of these formats:
    1. JSON array: [[lon1, lat1], [lon2, lat2], ...]
    2. CSV: lon,lat (one coordinate per line)
    3. Text: lon lat (one coordinate per line, space-separated)

    Args:
        file_path: Path to the file containing coordinates.

    Returns:
        List of coordinates as [lon, lat] pairs.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Coordinate file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8").strip()

    # Try JSON first
    try:
        coords = json.loads(content)
        if isinstance(coords, list) and len(coords) > 0:
            return coords
    except json.JSONDecodeError:
        pass

    # Try CSV or space-separated
    coordinates = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Try comma-separated first
        if "," in line:
            parts = [p.strip() for p in line.split(",")]
        else:
            # Space-separated
            parts = line.split()
        if len(parts) >= 2:
            try:
                lon, lat = float(parts[0]), float(parts[1])
                coordinates.append([lon, lat])
            except ValueError:
                continue

    if not coordinates:
        raise ValueError(
            f"Could not parse coordinates from file {file_path}. "
            "Expected JSON array, CSV (lon,lat), or space-separated (lon lat) format."
        )

    return coordinates


def polygon_from_coordinates(coordinates: Sequence[Sequence[float]]) -> Polygon:
    """
    Create a Polygon object from a list of points defining a polygon.

    Args:
        coordinates: List of coordinates, each as [lon, lat] or (lon, lat).
                     The polygon will be automatically closed if first != last point.

    Returns:
        Polygon object.

    Example:
        >>> coords = [[-74.006, 40.7128], [-73.935, 40.7128], [-73.935, 40.7589], [-74.006, 40.7589]]
        >>> polygon = polygon_from_coordinates(coords)
    """
    if len(coordinates) < 3:
        raise ValueError(
            f"A polygon requires at least 3 points, but got {len(coordinates)}."
        )

    # Convert coordinates to list of [lon, lat] pairs
    coord_list = []
    for coord in coordinates:
        if isinstance(coord, (list, tuple)) and len(coord) >= 2:
            coord_list.append([float(coord[0]), float(coord[1])])
        else:
            raise ValueError(
                f"Invalid coordinate format: {coord}. Expected [lon, lat] or (lon, lat)."
            )

    # Ensure polygon is closed (first point == last point)
    if coord_list[0] != coord_list[-1]:
        coord_list.append(coord_list[0])

    # Create and return Polygon from coordinates
    return Polygon(coord_list)


def create_geojson_from_points(
    coordinates: Sequence[Sequence[float]],
    output_path: Optional[Path] = None,
    name: Optional[str] = None,
) -> Path:
    """
    Create a GeoJSON file from a list of points defining a polygon.

    Args:
        coordinates: List of coordinates, each as [lon, lat] or (lon, lat).
                     The polygon will be automatically closed if first != last point.
        output_path: Optional path to save the GeoJSON file. If not provided,
                     a temporary file will be created.
        name: Optional name for the file (used if output_path is not provided).

    Returns:
        Path to the created GeoJSON file.

    Example:
        >>> coords = [[-74.006, 40.7128], [-73.935, 40.7128], [-73.935, 40.7589], [-74.006, 40.7589]]
        >>> geojson_path = create_geojson_from_points(coords, name="custom_polygon")
    """
    # Create polygon from coordinates
    polygon = polygon_from_coordinates(coordinates)

    # Determine output path
    if output_path is None:
        path = paths.geojson_path
        path.mkdir(parents=True, exist_ok=True)
        if name:
            filename = f"{name}.geojson"
        else:
            # Generate a temporary name
            filename = "polygon_from_points.geojson"
        output_path = path / filename
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as GeoJSON
    _polygon_to_geojson_file(polygon, output_path)
    return output_path


def get_polygon_from_geojson(geojson_path: str) -> Polygon | MultiPolygon:
    """Get a Polygon or MultiPolygon from a GeoJSON file."""
    with open(geojson_path) as gjf:
        features: list = json.load(gjf).get("features")

    if not features:
        raise ValueError(f"Features not found in GeoJSON {geojson_path}")

    if len(features) > 1:
        logger.warning(f"Found {len(features)} features. Be use first")

    first_feature, *_ = features
    if not first_feature.get("type") == "Feature":
        raise ValueError(
            f"Invalid feature type {first_feature.get('type')}. Expected 'Feature'"
        )

    geometry: dict = first_feature.get("geometry")
    geometry_type = geometry.get("type")

    if geometry_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(
            f"Invalid geometry type {geometry_type}. Expected 'Polygon' or 'MultiPolygon'"
        )

    coordinates: list = geometry.get("coordinates")
    if not coordinates:
        raise ValueError("Coordinates not found. Check GeoJSON")

    if geometry_type == "MultiPolygon":
        # MultiPolygon: create from list of polygons
        # Each element in coordinates is a polygon with its coordinate rings
        polygons = [Polygon(poly_coords[0]) for poly_coords in coordinates]
        polygon = MultiPolygon(polygons)
    else:
        # Polygon: handle single or multiple coordinate rings
        if len(coordinates) > 1:
            logger.warning(f"Found {len(coordinates)} coordinate rings. Using first")
        first_coords, *_ = coordinates
        polygon = Polygon(first_coords)

    return polygon


def get_map_geometry_from_poly(poly: Polygon | MultiPolygon) -> MapGeometry:
    """Get MapGeometry from a Polygon or MultiPolygon."""
    x1, y1, x2, y2 = poly.bounds
    top = max(y1, y2)
    bottom = min(y1, y2)
    left = min(x1, x2)
    right = max(x1, x2)
    center = [(top + bottom) / 2, (left + right) / 2]
    geometry = MapGeometry(
        top=top, bottom=bottom, left=left, right=right, center=center
    )
    return geometry
