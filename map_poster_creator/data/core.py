"""Core data processing functions."""

import os
import subprocess
from pathlib import Path
import platform
from requests import Session
from requests.adapters import HTTPAdapter
from typing import Optional
from urllib.parse import urljoin
import wget
from zipfile import ZipFile

from bs4 import BeautifulSoup, Tag
from ete3 import Tree
from shapely.geometry import Point
from pandas import DataFrame, Series
from unidecode import unidecode

from map_poster_creator.config import paths
from map_poster_creator.data.getters import (
    get_city_df,
    get_country_df,
    get_geofabrik_urls,
    get_region_polygons,
    get_region_centroids,
)
# Import geometry functions locally to avoid circular imports
# (geometry.py imports from data.getters, which creates a cycle)


GEOJSON_URL = "https://geojson.io/#map=10/{latitude}/{longitude}"
GEOFABRIK_URL = "https://download.geofabrik.de"
GEOFABRIK_HREF_ATTRIBUTE_END = "latest-free.shp.zip"


def is_valid_download_url(url: str) -> bool:
    """Check if URL is a valid GeoFabrik download URL."""
    return url.endswith(GEOFABRIK_HREF_ATTRIBUTE_END)


def is_valid_a_tag(a_tag: Tag) -> bool:
    """Check if an HTML tag is a valid download link."""
    return is_valid_download_url(a_tag.attrs["href"])


def _search_fun(df: DataFrame, search_term: str) -> Series:
    """Search function for finding cities in a DataFrame."""
    search_term_lower = search_term.lower()
    search_term_decoded = unidecode(search_term).lower()
    return (
        (df["asciiname"].apply(str.lower) == search_term_decoded)
        | (df["name"].apply(lambda x: unidecode(x).lower()) == search_term_decoded)
    ) | (
        df["alternatenames"]
        .apply(lambda x: x.split(","))
        .apply(lambda lst: any((x == search_term_lower) for x in lst))
    )


def resolve_city(
    city: str,
    country: Optional[str] = None,
    *,
    interactive: bool = True,
    element_if_one: bool = True,
    first: bool = False,
) -> DataFrame | Series | None:
    """
    Resolve a city name to a city record.

    Args:
        city: City name to search for
        country: Optional country name to narrow search
        interactive: If True, prompt user when multiple cities match
        element_if_one: If True and only one match, return the Series directly
        first: If True, always return the first (highest population) match

    Returns:
        DataFrame, Series, or None depending on matches and parameters
    """
    city_df = get_city_df()
    if country is None:
        candidates = city_df[_search_fun(city_df, city)].copy()
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
        from map_poster_creator.data.interactive import interactive_resolve_city

        return interactive_resolve_city(candidates)
    # Single candidate or first=True: return the first one
    if (candidates.shape[0] == 1 and element_if_one) or first:
        return candidates.iloc[0]
    return candidates


def _open_text_editor(file_path):
    """
    Opens a text editor with the specified file for the user to edit.
    Waits for the user to close the editor before continuing.
    """
    if platform.system() == "Windows":
        subprocess.run(["notepad", file_path], check=False)
    elif platform.system() == "Linux":
        subprocess.run(["nano", file_path], check=False)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", "-a", "TextEdit", file_path], check=False)
    else:
        raise SystemError(f"Unknown platform: {platform.system()}")


def _remove_hash_trailing_lines(file):
    """Remove lines starting with '#' from a file."""
    file.seek(0)
    edited_content = file.read().decode("utf-8").splitlines()
    filtered_content = [
        line for line in edited_content if not line.strip().startswith("#")
    ]
    file.seek(0)
    file.truncate()
    file.write("".join(filtered_content).encode("utf-8"))


def _ask_reuse(city):
    """Ask user if they want to reuse an existing GeoJSON file."""
    print(f"Geojson file found for {city}.")
    return input("Reuse? [Y/n] >").lower() not in {"n", "no", "false", "0"}


def _exit_if_empty_file(file):
    """Exit if the file is empty."""
    file.seek(0)
    if not file.read():
        raise SystemExit


def get_geojson_path_from_geoboundaries(
    city: str,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    interactive: bool = False,
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
            from map_poster_creator.data.interactive import interactive_resolve_city

            city_series = interactive_resolve_city(candidates)
        else:
            # Single candidate: take it
            city_series = candidates.iloc[0]
    else:
        # Use existing resolve_city function
        city_series = resolve_city(
            city=city, country=country, interactive=interactive, first=True
        )
        if city_series is None:
            raise ValueError(
                f'City "{city}" '
                + (f'and country "{country}" ' if country is not None else "")
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
    # Import from data.geometry (data-dependent) and geometry (pure utility)
    from map_poster_creator.data.geometry import _get_city_polygon_from_geoboundaries
    from map_poster_creator.geometry import _polygon_to_geojson_file

    try:
        polygon = _get_city_polygon_from_geoboundaries(city_series)
    except ValueError as e:
        raise ValueError(
            f'Could not find geoboundary for city "{city_name}" with country code "{resolved_country_code}". '
            f"Original error: {str(e)}"
        ) from e

    # Save polygon as geojson
    _polygon_to_geojson_file(polygon, filepath)
    return filepath


def _find_shp_url(region_url: str) -> str:
    """Find the SHP download URL from a GeoFabrik region page."""
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
        raise ValueError(f"Couldn't find a satisfying a tag in {region_url}.")


def _get_extract_dir(path: Path, fname: str) -> Path:
    """Get the extraction directory path for a zip file."""
    return path / Path(fname).stem


def _download_extract_shp(shp_url: str) -> Path:
    """Download and extract a SHP zip file."""
    path = paths.shp_path
    path.mkdir(parents=True, exist_ok=True)
    fname = shp_url.split("/")[-1]
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


def _extract_shp_url(node: Tree) -> str:
    """Extract the SHP URL for a region node."""
    geofabrik_urls = get_geofabrik_urls()
    for url in geofabrik_urls[node.name]:
        if is_valid_download_url(url):
            return url
    raise ValueError(f"Couldn't find a satisfying a tag for {node.name}.")


def _calculate_point_choose(city_point: Point, sorted_distances, city: str) -> Tree:
    """Calculate which region to choose based on point-in-polygon check."""
    # Import locally to avoid circular import
    from map_poster_creator.geometry import is_point_in_polygon

    for region_node, _ in sorted_distances:
        for region_polygon in get_region_polygons(region_node):
            if is_point_in_polygon(city_point, region_polygon):
                return region_node
    raise ValueError(f"Couldn't find a satisfying region for city {city}.")


def find_download_shp(
    city: str,
    country: Optional[str] = None,
    calculate_point: Optional[bool] = False,
    interactive: Optional[bool] = False,
) -> Path:
    """
    Find and download the SHP file for a city.

    Args:
        city: City name
        country: Optional country name
        calculate_point: If True, use point-in-polygon check to find region
        interactive: If True, prompt user to choose region

    Returns:
        Path to the extracted SHP directory
    """
    city_series = resolve_city(
        city=city, country=country, interactive=interactive, first=True
    )
    if city_series is None:
        raise ValueError(
            f'City "{city}" '
            + (f'and country "{country}" ' if country is not None else "")
            + "did not give any results."
        )
    city_point = Point(
        float(city_series["longitude"]),
        float(city_series["latitude"]),
    )
    distances = []
    for region_node, region_centroid_lst in get_region_centroids(
        only_leaf=True
    ).items():
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
        from map_poster_creator.data.interactive import interactive_region_choose

        region_node = interactive_region_choose(sorted_distances)
    else:
        region_node = sorted_distances[0][0]
    shp_url = _extract_shp_url(region_node)
    return _download_extract_shp(shp_url)
