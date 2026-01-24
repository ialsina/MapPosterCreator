from functools import lru_cache, cache
import json
import os
import subprocess
from pathlib import Path
import platform
from requests import Session
from requests.adapters import HTTPAdapter
from tempfile import NamedTemporaryFile
from typing import Optional, Sequence, Mapping, Callable
from urllib.parse import urljoin
import webbrowser
import wget
from zipfile import ZipFile

from bs4 import BeautifulSoup, Tag
from ete3 import Tree
from geopandas import GeoDataFrame
from shapely.geometry import Point, Polygon, MultiPolygon
from pandas import DataFrame, Series, read_csv
from unidecode import unidecode

from map_poster_creator.config import paths
from unidecode import unidecode


GEOJSON_URL = "https://geojson.io/#map=10/{latitude}/{longitude}"
GEOFABRIK_URL = "https://download.geofabrik.de"
GEOFABRIK_HREF_ATTRIBUTE_END = "latest-free.shp.zip"

def is_valid_download_url(url: str) -> bool:
    return url.endswith(GEOFABRIK_HREF_ATTRIBUTE_END)

def is_valid_a_tag(a_tag: Tag) -> bool:
    return is_valid_download_url(a_tag.attrs["href"])

@lru_cache(maxsize=None)
def get_city_df() -> DataFrame:
    if not paths.cities_geonames_1000.exists():
        raise FileNotFoundError(
            "Could not find city data. Please download using the appropriate script."
        )
    return read_csv(
        paths.cities_geonames_1000,
        index_col=0,
        low_memory=False
    ).fillna("")

@lru_cache(maxsize=None)
def get_country_df() -> DataFrame:
    if not paths.countries.exists():
        raise FileNotFoundError(
            "Could not find country data. Please download using the appropriate script."
        )
    return read_csv(paths.countries)

@lru_cache(maxsize=None)
def get_regions_tree() -> Tree:
    return Tree(str(paths.geofabrik_tree_nw), format=1)

@lru_cache(maxsize=None)
def get_geofabrik_urls() -> Mapping[str, str]:
    with open(paths.geofabrik_urls, "r", encoding="utf-8") as rf:
        return json.load(rf)

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

def is_point_in_polygon(point: Point, polygon: Polygon) -> bool:
    polygon_gdf = GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])
    point_gdf = GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[point])
    return bool(polygon_gdf.contains(
        point_gdf.loc[0, 'geometry']
    )[0])

@lru_cache(maxsize=None)
def get_region_polygons(node: Tree):
    if "polygon" not in node.features:
        return []
    try:
        return _parse_polygons(node.polygon)
    except ValueError as exc:
        return []

@lru_cache(maxsize=None)
def get_all_region_polygons(only_leaf: bool = False) -> Mapping[str, Sequence[Polygon]]:
    polygons = {}
    tree_iter = get_regions_tree().traverse()
    if tree_iter is None:
        return {}
    for node in tree_iter:
        if only_leaf and not node.is_leaf():
            continue
        polygons[node] = get_region_polygons(node)
    return polygons

@lru_cache(maxsize=None)
def get_region_centroids(only_leaf: bool = False) -> Mapping[str, Sequence[Point]]:
    polygons = get_all_region_polygons(only_leaf)
    centroids = {}
    for node, polygon_lst in polygons.items():
        centroids[node] = [
            polygon.centroid for polygon in polygon_lst
        ]
    return centroids

def _interactive_resolve_city(df: DataFrame) -> Series:
    def row_txt(row):
        country_name = countries[
            countries["Code"] == row["country code"]
        ].iloc[0]["Name"]
        admin_lst = [row[f"admin{i} code"] for i in range(4, 0, -1)]
        admin_lst.append(country_name)
        admin_txt = ", ".join(el for el in admin_lst if el)
        return f"{row['name']}, {admin_txt}"
    countries = get_country_df()
    choices = {i: row for i, (_, row) in enumerate(df.iterrows(), start=1)}
    print("Choose city:")
    print("\t" + "\n\t".join(
        f"{i}. {row_txt(row)}" for i, row in choices.items()
    ))
    while True:
        user_input = input("\tSelect choice [1] >")
        if user_input == "":
            return choices[1]
        try:
            user_input = int(user_input)
            if user_input in choices:
                return choices[user_input]
        except ValueError:
            pass

def _search_fun(df: DataFrame, search_term: str) -> Series:
    search_term_lower = search_term.lower()
    search_term_decoded = unidecode(search_term).lower()
    return ((
        df["asciiname"].apply(str.lower) == search_term_decoded
    ) | (
        df["name"].apply(lambda x: unidecode(x).lower()) == search_term_decoded
    )) | (
        df["alternatenames"].apply(
            lambda x: x.split(",")
        ).apply(lambda lst: any(
            (x == search_term_lower) for x in lst
        ))
    )

def resolve_city(
        city: str,
        country: Optional[str] = None,
        *,
        interactive: bool = True,
        element_if_one: bool = True,
        first: bool = False,
    ) -> DataFrame | Series | None:
    city_df = get_city_df()
    if country is None:
        candidates = city_df[
            _search_fun(city_df, city)
        ].copy()
    else:
        countries = get_country_df()
        country_code = countries[
            countries["Name"].apply(str.lower) == country.lower()
        ].iloc[0]["Code"]
        candidates = city_df[
            (city_df["asciiname"].apply(str.lower) == unidecode(city).lower())
            & (city_df["country code"] == country_code)
        ].copy()
    candidates.sort_values(by="population", ascending=False, inplace=True)
    if candidates.shape[0] == 0:
        return None
    # If interactive is False, always return the first (highest population) without prompting
    if not interactive:
        return candidates.iloc[0]
    # Interactive mode: prompt if multiple candidates
    if candidates.shape[0] > 1:
        return _interactive_resolve_city(candidates)
    # Single candidate or first=True: return the first one
    if (candidates.shape[0] == 1 and element_if_one) or first:
        return candidates.iloc[0]
    return candidates

def _open_text_editor(file_path):
    """
    Opens a text editor with the specified file for the user to edit.
    Waits for the user to close the editor before continuing.
    """
    if platform.system() == 'Windows':
        subprocess.run(['notepad', file_path], check=False)
    elif platform.system() == 'Linux':
        subprocess.run(['nano', file_path], check=False)
    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(['open', '-a', 'TextEdit', file_path], check=False)
    else:
        raise SystemError(
            f"Unknown platform: {platform.system()}"
        )

def _remove_hash_trailing_lines(file):
    file.seek(0)
    edited_content = file.read().decode("utf-8").splitlines()
    filtered_content = [line for line in edited_content if not line.strip().startswith('#')]
    file.seek(0)
    file.truncate()
    file.write("".join(filtered_content).encode("utf-8"))

def _ask_reuse(city):
    print(f"Geojson file found for {city}.")
    return input("Reuse? [Y/n] >").lower() not in {"n", "no", "false", "0"}

def _exit_if_empty_file(file):
    file.seek(0)
    if not file.read():
        raise SystemExit

@cache
def get_geoboundaries_gdf() -> GeoDataFrame:
    """Load and cache the geoboundaries GeoDataFrame."""
    if not paths.geoboundaries_path.exists():
        raise FileNotFoundError(
            "Could not find geoboundaries data. Please ensure geoBoundariesCGAZ_ADM2.geojson exists."
        )
    gdf = GeoDataFrame.from_file(paths.geoboundaries_path)
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

@cache
def get_cities_geonames() -> DataFrame:
    """Load and cache the cities geonames DataFrame."""
    if not paths.cities_geonames_1000.exists():
        raise FileNotFoundError(
            "Could not find city data. Please download using the appropriate script."
        )
    return read_csv(paths.cities_geonames_1000, index_col=0, low_memory=False)

def _get_city_point_from_series(city_series: Series) -> Point:
    """Get a Point geometry for a city from a resolved city Series."""
    lat = city_series["latitude"]
    lon = city_series["longitude"]
    return Point(lon, lat)

def _get_city_polygon_from_geoboundaries(city_series: Series) -> Polygon | MultiPolygon:
    """Get the administrative boundary polygon for a city from geoboundaries."""
    pt = _get_city_point_from_series(city_series)
    gdf = get_geoboundaries_gdf()
    
    # Use spatial index to get possible matches
    possible_matches_index = list(gdf.sindex.intersection(pt.bounds))
    if not possible_matches_index:
        city_name = city_series.get("name", "unknown")
        country_code = city_series.get("country code", "unknown")
        raise ValueError(
            f'No geoboundaries found near city "{city_name}" with country code "{country_code}".'
        )
    possible_matches = gdf.iloc[possible_matches_index]
    
    # Filter precisely
    city_poly = possible_matches[possible_matches.contains(pt)]
    
    if city_poly.empty:
        city_name = city_series.get("name", "unknown")
        country_code = city_series.get("country code", "unknown")
        raise ValueError(
            f'No polygon found containing city "{city_name}" with country code "{country_code}".'
        )
    
    # Return the first matching polygon's geometry (could be Polygon or MultiPolygon)
    return city_poly.iloc[0].geometry

def _polygon_to_geojson_file(geometry: Polygon | MultiPolygon, filepath: Path) -> None:
    """Save a Polygon or MultiPolygon to a GeoJSON file."""
    def convert_coord(coord):
        """Convert a coordinate to [lon, lat] format."""
        try:
            # Try to convert to tuple/list first if it's a numpy array or similar
            if hasattr(coord, 'tolist'):
                coord = coord.tolist()
            # Handle tuple, list, or any sequence
            if hasattr(coord, '__getitem__') and hasattr(coord, '__len__'):
                if len(coord) >= 2:
                    return [float(coord[0]), float(coord[1])]
            # If it's already a float or single value, that's an error
            raise ValueError(f"Unexpected coordinate format: {coord} (type: {type(coord)})")
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
                "geometry": {
                    "type": geometry_type,
                    "coordinates": coordinates
                },
                "properties": {}
            }
        ]
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
        if not line or line.startswith('#'):
            continue
        # Try comma-separated first
        if ',' in line:
            parts = [p.strip() for p in line.split(',')]
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

def polygon_from_coordinates(
    coordinates: Sequence[Sequence[float]]
) -> Polygon:
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
    name: Optional[str] = None
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

def get_geojson_path_from_geoboundaries(
    city: str, 
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    interactive: bool = False
) -> Path:
    """
    Get geojson path by automatically finding the city polygon from geoboundaries.
    
    Args:
        city: City name
        country: Country name (optional, used if country_code is not provided)
        country_code: Two-letter country code (optional, takes precedence over country)
        interactive: If True, prompt user when multiple cities match. If False, use highest population.
    
    Returns:
        Path to the generated GeoJSON file
    """
    path = paths.geojson_path
    path.mkdir(parents=True, exist_ok=True)
    
    # Resolve city - use country_code if provided, otherwise use country name
    # Check if country_code is provided and not empty
    if country_code is not None and str(country_code).strip():
        # Direct lookup with country_code using the same search logic as resolve_city
        city_df = get_city_df()
        # First filter by city name using search function
        candidates = city_df[_search_fun(city_df, city)].copy()
        # Then filter by country code (ensure both are uppercase for comparison)
        country_code_upper = country_code.upper().strip()
        candidates = candidates[
            candidates["country code"].str.upper().str.strip() == country_code_upper
        ].copy()
        candidates.sort_values(by="population", ascending=False, inplace=True)
        
        if candidates.shape[0] == 0:
            raise ValueError(
                f'City "{city}" with country code "{country_code}" did not give any results.'
            )
        
        # If interactive is False, always take the highest population without prompting
        if not interactive:
            city_series = candidates.iloc[0]
        elif candidates.shape[0] > 1:
            # Interactive mode with multiple candidates: prompt user
            city_series = _interactive_resolve_city(candidates)
        else:
            # Single candidate: take it
            city_series = candidates.iloc[0]
    else:
        # Use existing resolve_city function
        city_series = resolve_city(
            city=city, 
            country=country, 
            interactive=interactive, 
            first=True
        )
        if city_series is None:
            raise ValueError(
                f'City "{city}" '
                + (f'and country "{country}" ' if country is not None else '')
                + "did not give any results."
            )
    
    resolved_country_code = city_series["country code"]
    city_name = city_series["name"]
    

    # Create filename based on city and country
    filename = f"{city_name}_{resolved_country_code}.geojson"
    filepath = path / filename

    # Check if file already exists
    if filepath.exists():
        if interactive:
            # In interactive mode, ask user if they want to reuse
            if _ask_reuse(city):
                return filepath
        else:
            # In non-interactive mode, automatically reuse existing file
            return filepath
    
    # Get polygon from geoboundaries
    try:
        polygon = _get_city_polygon_from_geoboundaries(city_series)
    except ValueError as e:
        raise ValueError(
            f'Could not find geoboundary for city "{city_name}" with country code "{resolved_country_code}". '
            f'Original error: {str(e)}'
        ) from e
    
    # Save polygon as geojson
    _polygon_to_geojson_file(polygon, filepath)
    return filepath

def browser_get_geojson_path_interactive(city: str, country: Optional[str] = None) -> Path:
    path = paths.geojson_path
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{city}.geojson"
    if filepath.exists():
        if _ask_reuse(city):
            return filepath
    city_series = resolve_city(city=city, country=country)
    if city_series is None:
        raise ValueError(
            f'City "{city}" '
            + (f'and country "{country}" ' if country is not None else '')
            + "did not give any results."
        )
    webbrowser.open_new_tab(
        GEOJSON_URL.format(
            latitude=city_series["latitude"],
            longitude=city_series["longitude"])
    )
    with open(filepath, "w+b") as tf:
        filepath = tf.name
        tf.write(
            b"# Create the shape in the browser, and paste the JSON object below\n\n\n"
        )
        tf.flush()
        _open_text_editor(filepath)
        _remove_hash_trailing_lines(tf)
        _exit_if_empty_file(tf)
    return Path(filepath)

def _find_shp_url(region_url: str) -> str:
    with Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        response = session.get(region_url)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            raise IOError(
                f"Could not fetch resource (status code: {response.status_code}): "
                + str(region_url)
            )
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", recursive=True):
            if is_valid_a_tag(a_tag):
                return urljoin(region_url, a_tag.attrs["href"])
        raise ValueError(
            f"Couldn't find a satisfying a tag in {region_url}."
        )

def _get_extract_dir(path: Path, fname: str) -> Path:
    return (path / Path(fname).stem)

def _download_extract_shp(shp_url: str) -> Path:
    path = paths.shp_path
    path.mkdir(parents=True, exist_ok=True)
    fname = shp_url.split('/')[-1]
    if _get_extract_dir(path, fname).exists():
        return _get_extract_dir(path, fname)
    print(f"Downloading in: {path}")
    fname = wget.download(shp_url, out=str(path))
    zip_fpath = path / fname
    print(f"New zip file: {zip_fpath}")
    extract_dir = _get_extract_dir(path, fname)
    extract_dir.mkdir(parents=False, exist_ok=False)
    print(f"Extracting in: {extract_dir}")
    with ZipFile(zip_fpath, "r") as zf:
        zf.extractall(path=str(extract_dir))
    os.remove(zip_fpath)
    return extract_dir

def download_shp_interactive(city: str, country: Optional[str] = None) -> Path:
    webbrowser.open_new_tab(GEOFABRIK_URL)
    message = (
        "# Please, navigate to the page of the region corresponding to the city of "
        f"{city}{f', {country}' if country is not None else ''}.\n"
        "# Then, paste the URL below\n\n\n"
    )
    with NamedTemporaryFile(mode="w+b", delete=False) as tf:
        tf.write(message.encode("utf-8"))
        tf.flush()
        _open_text_editor(tf.name)
        _remove_hash_trailing_lines(tf)
        tf.seek(0)
        region_url = tf.read().decode("utf-8").strip()
        shp_url = _find_shp_url(region_url)
    extract_dir = _download_extract_shp(shp_url)
    return extract_dir

def _extract_shp_url(node: Tree):
    geofabrik_urls = get_geofabrik_urls()
    for url in geofabrik_urls[node.name]:
        if is_valid_download_url(url):
            return url
    raise ValueError(
        f"Couldn't find a satisfying a tag for {node.name}."
    )

def _interactive_region_choose(sorted_distances, num_choices=5) -> Tree:
    top_regions = list(zip(*sorted_distances))[0][:num_choices]
    choices = {i: region for i, region in enumerate(top_regions, start=1)}
    print("Choose region:")
    print("\t" + "\n\t".join(
        f"{i}. {node.name}" for i, node in choices.items())
    )
    while True:
        user_input = input("\tSelect choice [1] >")
        if user_input == "":
            return choices[1]
        try:
            user_input = int(user_input)
            if user_input in choices:
                return choices[user_input]
        except ValueError:
            pass

def _calculate_point_choose(city_point, sorted_distances, city) -> Tree:
    for region_node, _ in sorted_distances:
        for region_polygon in get_region_polygons(region_node):
            if is_point_in_polygon(city_point, region_polygon):
                return region_node
    raise ValueError(
        f"Couldn't find a satisfying region for city {city}."
    )

def find_download_shp(
        city: str,
        country: Optional[str] = None,
        calculate_point: Optional[bool] = False,
        interactive: Optional[bool] = False,
    ):
    city_series = resolve_city(city=city, country=country, interactive=interactive, first=True)
    if city_series is None:
        raise ValueError(
            f'City "{city}" '
            + (f'and country "{country}" ' if country is not None else '')
            + "did not give any results."
        )
    city_point = Point(
        float(city_series["longitude"]),
        float(city_series["latitude"]),
    )
    distances = []
    for region_node, region_centroid_lst in get_region_centroids(only_leaf=True).items():
        try:
            distance = min(
                city_point.distance(region_centroid)
                for region_centroid in region_centroid_lst
            )
            distances.append((region_node, distance))
        except ValueError:
            continue
    sorted_distances = sorted(distances, key=lambda x: x[1], reverse=False)
    if calculate_point:
        region_node = _calculate_point_choose(city_point, sorted_distances, city)
    elif interactive:
        region_node = _interactive_region_choose(sorted_distances)
    else:
        region_node = sorted_distances[0][0]
    shp_url = _extract_shp_url(region_node)
    return _download_extract_shp(shp_url)

