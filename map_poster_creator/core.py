from dataclasses import dataclass

from typing import Tuple, Sequence, Optional
from pathlib import Path

from geopandas import GeoDataFrame
from shapely.geometry import Polygon, MultiPolygon

from map_poster_creator.colorscheme import ColorScheme
from map_poster_creator.geojson import (
    get_polygon_from_geojson,
    get_map_geometry_from_poly,
    MapGeometry
)
from map_poster_creator.logs import log_processing, logging
from map_poster_creator.plotting import plot_and_save
from map_poster_creator.data import create_geojson_from_points, polygon_from_coordinates

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class shp_filename:
    roads = "gis_osm_roads_free_1.shp"
    water = "gis_osm_water_a_free_1.shp"
    greens = "gis_osm_pois_a_free_1.shp"


@log_processing
def _get_boundary_shape(geojson_or_polygon: Path | str | Polygon | MultiPolygon) -> Tuple[Polygon | MultiPolygon, MapGeometry]:
    """
    Extract polygon and geometry from either a GeoJSON file path or a Polygon/MultiPolygon object.
    """
    if isinstance(geojson_or_polygon, (Polygon, MultiPolygon)):
        poly = geojson_or_polygon
    else:
        poly = get_polygon_from_geojson(geojson_or_polygon)
    geometry = get_map_geometry_from_poly(poly)
    return poly, geometry

@log_processing
def _preprocessing(poly: Polygon | MultiPolygon, gdf: GeoDataFrame) -> GeoDataFrame:
    def poly_contains(g):
        return poly.contains(g)
    town = gdf.loc[
        gdf['geometry'].apply(poly_contains)
    ].copy()
    return town

@log_processing
def _preprocessing_roads(poly: Polygon | MultiPolygon, gdf: GeoDataFrame) -> GeoDataFrame:
    town = _preprocessing(poly=poly, gdf=gdf)
    town = town[~town.fclass.isin(['footway', "steps"])]
    town['speeds'] = [speed for speed in town['maxspeed']]
    return town

def create_poster(
        shp_dir: Path,
        geojson_path: Path | str | Polygon | MultiPolygon,
        color: ColorScheme,
        width: int | float,
        dpi: int,
        output: Path,
):
    """
    Create a map poster from a polygon boundary.
    
    Args:
        shp_dir: Path to directory containing shapefiles (roads, water, greens).
        geojson_path: Path to GeoJSON file, or a Polygon/MultiPolygon object directly.
        color: ColorScheme to use for the poster.
        width: Width of the figure in inches.
        dpi: Dots per inch (dpi) of the figure.
        output: Path where the poster image will be saved.
    """
    poly, geometry = _get_boundary_shape(geojson_or_polygon=geojson_path)
    roads = _preprocessing_roads(
        poly=poly,
        gdf=GeoDataFrame.from_file(shp_dir / shp_filename.roads, encoding="utf-8")
    )
    water = _preprocessing(
        poly=poly,
        gdf=GeoDataFrame.from_file(shp_dir / shp_filename.water, encoding="utf-8")
    )
    greens = _preprocessing(
        poly=poly,
        gdf=GeoDataFrame.from_file(shp_dir / shp_filename.greens, encoding="utf-8")
    )
    plot_and_save(
        roads=roads,
        water=water,
        greens=greens,
        geometry=geometry,
        path=output,
        dpi=dpi,
        width=width,
        cscheme=color,
    )

def create_poster_from_coordinates(
        shp_dir: Path,
        coordinates: Sequence[Sequence[float]],
        color: ColorScheme,
        width: int | float,
        dpi: int,
        output: Path,
        geojson_output_path: Optional[Path] = None,
):
    """
    Create a poster from a list of coordinates defining a polygon.
    
    This function creates a Polygon object from coordinates and passes it directly
    to create_poster, avoiding the need to create a GeoJSON file unless explicitly requested.
    
    Args:
        shp_dir: Path to directory containing shapefiles (roads, water, greens).
        coordinates: List of coordinates, each as [lon, lat] or (lon, lat).
                     The polygon will be automatically closed if first != last point.
        color: ColorScheme to use for the poster.
        width: Width of the figure in inches.
        dpi: Dots per inch (dpi) of the figure.
        output: Path where the poster image will be saved.
        geojson_output_path: Optional path to save the intermediate GeoJSON file.
                            If not provided, the polygon is passed directly without creating a file.
    
    Example:
        >>> from map_poster_creator.core import create_poster_from_coordinates
        >>> from map_poster_creator.colorscheme import get_colorscheme
        >>> coords = [[-74.006, 40.7128], [-73.935, 40.7128], [-73.935, 40.7589], [-74.006, 40.7589]]
        >>> create_poster_from_coordinates(
        ...     shp_dir=Path("/path/to/shp"),
        ...     coordinates=coords,
        ...     color=get_colorscheme("white"),
        ...     width=15,
        ...     dpi=300,
        ...     output=Path("poster.png")
        ... )
    """
    # Create polygon from coordinates
    polygon = polygon_from_coordinates(coordinates)
    
    # If geojson_output_path is provided, save the polygon to a file first
    if geojson_output_path is not None:
        from map_poster_creator.data import _polygon_to_geojson_file
        _polygon_to_geojson_file(polygon, geojson_output_path)
        geojson_or_polygon = geojson_output_path
    else:
        # Pass the polygon object directly - no file creation needed
        geojson_or_polygon = polygon
    
    create_poster(
        shp_dir=shp_dir,
        geojson_path=geojson_or_polygon,
        color=color,
        width=width,
        dpi=dpi,
        output=output,
    )

