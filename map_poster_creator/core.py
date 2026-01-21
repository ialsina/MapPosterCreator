from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame
from shapely.geometry import MultiPolygon, Polygon

from map_poster_creator.colorscheme import ColorScheme
from map_poster_creator.geojson import (
    MapGeometry,
    get_map_geometry_from_poly,
    get_polygon_from_geojson,
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
def _get_boundary_shape(geojson) -> tuple[Polygon | MultiPolygon, MapGeometry]:
    poly = get_polygon_from_geojson(geojson)
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
    geojson_path: Path,
    color: ColorScheme,
    width: int | float,
    dpi: int,
    output: Path,
):
    poly, geometry = _get_boundary_shape(geojson=geojson_path)
    print(poly)
    print(geometry)
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
