from shapely.geometry import Point

from map_poster_creator.data.getters import get_geoboundaries_gdf, get_cities_geonames


def get_city_polygon(city_name, country_code):
    df = get_cities_geonames()
    city = df[(df["name"] == city_name) & (df["country_code"] == country_code)].iloc[0]
    lat = city["latitude"]
    lon = city["longitude"]
    pt = Point(lon, lat)
    return pt


city_polygon = get_city_polygon("Tokyo", "JP")
gdf = get_geoboundaries_gdf()

# Use spatial index to get possible matches
possible_matches_index = list(gdf.sindex.intersection(city_polygon.bounds))
possible_matches = gdf.iloc[possible_matches_index]

# Filter precisely
city_poly = possible_matches[possible_matches.contains(city_polygon)]

if city_poly.empty:
    print("No polygon found for this point.")
else:
    print(city_poly.iloc[0])
