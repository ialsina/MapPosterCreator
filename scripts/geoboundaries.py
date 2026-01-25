from shapely.geometry import Point
from geopandas import GeoDataFrame

from map_poster_creator.data.models import _geoboundaries_gdf, _cities_geonames

def get_geoboundaries_gdf():
    """Get geoboundaries GeoDataFrame from the model."""
    return _geoboundaries_gdf.data

def get_cities_geonames():
    """Get cities GeoNames DataFrame from the model."""
    return _cities_geonames.data

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
