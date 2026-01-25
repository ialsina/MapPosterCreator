from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame
from shapely.geometry import MultiPolygon, Polygon

from map_poster_creator.colorscheme import ColorScheme
from map_poster_creator.geometry import (
    MapGeometry,
    get_map_geometry_from_poly,
    get_polygon_from_geojson,
    polygon_from_coordinates,
)
from map_poster_creator.logs import log_processing, logging
from map_poster_creator.plotting import plot_and_save

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class shp_filename:
    roads = "gis_osm_roads_free_1.shp"
    water = "gis_osm_water_a_free_1.shp"
    greens = "gis_osm_pois_a_free_1.shp"


@log_processing
def _get_boundary_shape(
    geojson_or_polygon: Path | str | Polygon | MultiPolygon,
) -> tuple[Polygon | MultiPolygon, MapGeometry]:
    """Extract polygon and geometry from a GeoJSON path or polygon object."""
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

    town = gdf.loc[gdf["geometry"].apply(poly_contains)].copy()
    return town


@log_processing
def _preprocessing_roads(poly: Polygon | MultiPolygon, gdf: GeoDataFrame) -> GeoDataFrame:
    town = _preprocessing(poly=poly, gdf=gdf)
    town = town[~town.fclass.isin(["footway", "steps"])]
    town["speeds"] = [speed for speed in town["maxspeed"]]
    return town


def create_poster(
    shp_dir: Path,
    geojson_path: Path | str | Polygon | MultiPolygon,
    color: ColorScheme,
    width: int | float,
    dpi: int,
    output: Path,
):
    """Create a map poster from a polygon boundary."""
    poly, geometry = _get_boundary_shape(geojson_or_polygon=geojson_path)
    roads = _preprocessing_roads(
        poly=poly,
        gdf=GeoDataFrame.from_file(shp_dir / shp_filename.roads, encoding="utf-8"),
    )
    water = _preprocessing(
        poly=poly,
        gdf=GeoDataFrame.from_file(shp_dir / shp_filename.water, encoding="utf-8"),
    )
    greens = _preprocessing(
        poly=poly,
        gdf=GeoDataFrame.from_file(shp_dir / shp_filename.greens, encoding="utf-8"),
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
    geojson_output_path: Path | None = None,
):
    """Create a poster from a list of coordinates defining a polygon."""
    polygon = polygon_from_coordinates(coordinates)

    if geojson_output_path is not None:
        from map_poster_creator.geometry import _polygon_to_geojson_file

        _polygon_to_geojson_file(polygon, geojson_output_path)
        geojson_or_polygon = geojson_output_path
    else:
        geojson_or_polygon = polygon

    create_poster(
        shp_dir=shp_dir,
        geojson_path=geojson_or_polygon,
        color=color,
        width=width,
        dpi=dpi,
        output=output,
    )
