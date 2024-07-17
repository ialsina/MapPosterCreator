from collections import defaultdict
from ete3 import Tree
import geopandas as gpd
import json
from pandas import read_csv, DataFrame
from shapely.geometry import Point, Polygon
from typing import Iterable, Sequence, Mapping
from tqdm import tqdm

from map_poster_creator.config import paths

def _parse_polygons(data: str) -> Sequence[Polygon]:
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

def find_regions(tree: Tree, country: str) -> Iterable[str]:
    tree_iter = tree.traverse()
    if tree_iter is None:
        return iter([])
    for node in tree_iter:
        if node.name == country:
            node_iter = node.traverse()
            if node_iter is None:
                return iter([])
            return (child.name for child in node_iter)
    return iter([])

def get_region_polygons(tree: Tree) -> Mapping[str, Sequence[Polygon]]:
    polygons = {}
    tree_iter = tree.traverse()
    if tree_iter is None:
        return {}
    for node in tree_iter:
        if "polygon" not in node.features:
            polygons[node.name] = []
            continue
        try:
            polygons[node.name] = _parse_polygons(node.polygon)
        except ValueError as exc:
            polygons[node.name] = []
    return polygons

def get_region_centroids(polygons: Mapping[str, Sequence[Polygon]]) -> Mapping[str, Sequence[Point]]:
    centroids = {}
    for region, polygon_lst in polygons.items():
        centroids[region] = [polygon.centroid for polygon in polygon_lst]
    return centroids

def is_point_in_polygon(point: Point, polygon: Polygon) -> bool:
    polygon_gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])
    point_gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[point])
    return polygon_gdf.contains(point_gdf.loc[0, 'geometry'])[0]

print("Reading cities...")
cities = read_csv(paths.cities_geonames_1000, low_memory=False, index_col=0)
print("Reading subregions...")
regions = Tree(str(paths.geofabrik_tree_nw), format=1)
print("Reading countries...")
countries = read_csv(paths.countries)
print("Defining subregion polygons...")
region_polygons = get_region_polygons(regions)
print("Defining subregion centroids...")
region_centroids = get_region_centroids(region_polygons)

print("Matching cities and polygons...")
city_regions = defaultdict(list)
city_distances = {}
with tqdm(total=cities.shape[0], leave=True) as pbar:
    for _, row in cities.iterrows():
        city = row["asciiname"]
        country = countries[
            countries["Code"] == row["country code"]
        ].iloc[0]["Name"]
        pbar.set_description(f"{f'{country}'}, {f'{city}':<30s}")
        city_point = Point(row.longitude , row.latitude)
        for region in find_regions(regions, country):
            if any(
                is_point_in_polygon(city_point, polygon)
                for polygon in region_polygons[region]
            ):
                city_regions[city].append(region)
        pbar.update()

with open("city_regions.json", "w", encoding="utf-8") as f:
    json.dump(city_regions, f)
