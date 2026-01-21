from shapely.geometry import Point
from geopandas import GeoDataFrame
from pandas import read_csv
from functools import cache

from map_poster_creator.config import paths

@cache
def get_geoboundaries_gdf():
    gdf = GeoDataFrame.from_file(paths.geoboundaries_path)
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

@cache
def get_cities_geonames():
    return read_csv(paths.cities_geonames_1000, index_col=0, low_memory=False)

def get_city_polygon(city_name, country_code):
    df = get_cities_geonames()
    city = df[
        (df["name"] == city_name) &
        (df["country_code"] == country_code)
    ].iloc[0]
    lat = city["latitude"]
    lon = city["longitude"]
    pt = Point(lon, lat)
    return pt

city_polygon = get_city_polygon("Tokyo", "JP")

# Use spatial index to get possible matches
possible_matches_index = list(gdf.sindex.intersection(pt.bounds))
possible_matches = gdf.iloc[possible_matches_index]

# Filter precisely
city_poly = possible_matches[possible_matches.contains(pt)]

if city_poly.empty:
    print("No polygon found for this point.")
else:
    print(city_poly.iloc[0])
