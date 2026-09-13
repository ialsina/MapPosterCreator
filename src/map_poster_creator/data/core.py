"""Core data processing functions."""

from pathlib import Path
from typing import Optional, Callable

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
from map_poster_creator.data.utils import (
    _ask_reuse,
    _download_extract_shp,
    is_valid_download_url,
)

# Geometry imports at module level (no circular dependency)
from map_poster_creator.data.geometry import _get_city_polygon_from_geoboundaries
from map_poster_creator.geometry import (
    is_point_in_polygon,
    _polygon_to_geojson_file,
)


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
    interactive_callback: Optional[Callable[[DataFrame], Series]] = None,
) -> DataFrame | Series | None:
    """
    Resolve a city name to a city record.

    Args:
        city: City name to search for
        country: Optional country name to narrow search
        interactive: If True, prompt user when multiple cities match (requires interactive_callback)
        element_if_one: If True and only one match, return the Series directly
        first: If True, always return the first (highest population) match
        interactive_callback: Optional callback function for interactive city selection.
                            Called with DataFrame of candidates, should return selected Series.

    Returns:
        DataFrame, Series, or None depending on matches and parameters
    """
    city_df = get_city_df()
    if country is None:
        candidates = city_df[_search_fun(city_df, city)].copy()
    else:
        countries = get_country_df()
        country_matches = countries[
            countries["Name"].apply(str.lower) == country.lower()
        ]
        if country_matches.shape[0] == 0:
            raise ValueError(f'Country "{country}" not found in database.')
        country_code = country_matches.iloc[0]["Code"]
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
        if interactive_callback is not None:
            return interactive_callback(candidates)
        # No callback provided, return first (non-interactive fallback)
        return candidates.iloc[0]
    # Single candidate or first=True: return the first one
    if (candidates.shape[0] == 1 and element_if_one) or first:
        return candidates.iloc[0]
    return candidates


def get_geojson_path_from_geoboundaries(
    city: str,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    interactive: bool = False,
    interactive_callback: Optional[Callable[[DataFrame], Series]] = None,
) -> Path:
    """
    Get geojson path by automatically finding the city polygon from geoboundaries.

    Args:
        city: City name
        country: Country name (optional, used if country_code is not provided)
        country_code: Two-letter country code (optional, takes precedence over country)
        interactive: If True, prompt user when multiple cities match. If False, use highest population.
        interactive_callback: Optional callback function for interactive city selection.
                            Called with DataFrame of candidates, should return selected Series.

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
            if interactive and interactive_callback is not None:
                city_series = interactive_callback(candidates)
            else:
                city_series = candidates.iloc[0]
        else:
            # Single candidate: take it
            city_series = candidates.iloc[0]
    else:
        # Use existing resolve_city function
        city_series = resolve_city(
            city=city,
            country=country,
            interactive=interactive,
            first=True,
            interactive_callback=interactive_callback,
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


def _extract_shp_url(node: Tree) -> str:
    """Extract the SHP URL for a region node."""
    geofabrik_urls = get_geofabrik_urls()
    for url in geofabrik_urls[node.name]:
        if is_valid_download_url(url):
            return url
    raise ValueError(f"Couldn't find a satisfying a tag for {node.name}.")


def _calculate_point_choose(
    point: Point, sorted_distances, location_name: str = "point"
) -> Tree:
    """
    Calculate which region to choose based on point-in-polygon check.
    
    Ensures the selected node is a leaf node (only leaf nodes have polygons).
    The sorted_distances should already contain only leaf nodes, but we verify.
    """
    for region_node, _ in sorted_distances:
        # Verify this is a leaf node (defensive check)
        if not region_node.is_leaf():
            continue
        for region_polygon in get_region_polygons(region_node):
            if is_point_in_polygon(point, region_polygon):
                return region_node
    raise ValueError(f"Couldn't find a satisfying region for {location_name}.")


def find_download_shp_from_point(
    point: Point,
    calculate_point: Optional[bool] = False,
    interactive: Optional[bool] = False,
    location_name: str = "point",
    interactive_callback: Optional[Callable[[list], Tree]] = None,
) -> Path:
    """
    Find and download the SHP file for a geographic point.

    Args:
        point: Geographic point (Point with longitude, latitude)
        calculate_point: If True, use point-in-polygon check to find region
        interactive: If True, prompt user to choose region (requires interactive_callback)
        location_name: Name of the location for error messages (default: "point")
        interactive_callback: Optional callback function for interactive region selection.
                            Called with list of (region_node, distance) tuples, should return selected Tree.

    Returns:
        Path to the extracted SHP directory
    """
    distances = []
    # Get centroids for leaf nodes only (only leaf nodes represent actual regions)
    for region_node, region_centroid_lst in get_region_centroids(
        only_leaf=True
    ).items():
        # Defensive check: ensure this is actually a leaf node
        if not region_node.is_leaf():
            continue
        try:
            # Calculate minimum distance to any centroid of this region
            # (regions can have multiple polygons, so we take the closest one)
            distance = min(
                point.distance(region_centroid)
                for region_centroid in region_centroid_lst
            )
            distances.append((region_node, distance))
        except ValueError:
            continue
    
    # Sort by distance (closest first)
    sorted_distances = sorted(distances, key=lambda x: x[1], reverse=False)
    
    if len(sorted_distances) == 0:
        raise ValueError(
            f"No regions found for {location_name}. "
            "This may indicate that region data is not properly initialized."
        )
    
    # Select the region node based on the method
    if calculate_point:
        # Use point-in-polygon check to find the region that actually contains the point
        # This is more accurate than just distance to centroid
        region_node = _calculate_point_choose(point, sorted_distances, location_name)
    elif interactive:
        if interactive_callback is not None:
            region_node = interactive_callback(sorted_distances)
        else:
            # No callback provided, use closest node (non-interactive fallback)
            region_node = sorted_distances[0][0]
    else:
        # Default: use the closest leaf node spatially (by centroid distance)
        region_node = sorted_distances[0][0]
    
    # Final verification: ensure we selected a leaf node
    if not region_node.is_leaf():
        raise ValueError(
            f"Selected region node '{region_node.name if hasattr(region_node, 'name') else 'unknown'}' "
            f"is not a leaf node. This should not happen as only leaf nodes should be considered."
        )
    shp_url = _extract_shp_url(region_node)
    return _download_extract_shp(shp_url)


def find_download_shp(
    city: str,
    country: Optional[str] = None,
    calculate_point: Optional[bool] = False,
    interactive: Optional[bool] = False,
    interactive_callback: Optional[Callable[[DataFrame], Series]] = None,
    region_callback: Optional[Callable[[list], Tree]] = None,
) -> Path:
    """
    Find and download the SHP file for a city.

    Args:
        city: City name
        country: Optional country name
        calculate_point: If True, use point-in-polygon check to find region
        interactive: If True, prompt user to choose region (requires callbacks)
        interactive_callback: Optional callback for interactive city selection
        region_callback: Optional callback for interactive region selection

    Returns:
        Path to the extracted SHP directory
    """
    city_series = resolve_city(
        city=city,
        country=country,
        interactive=interactive,
        first=True,
        interactive_callback=interactive_callback,
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
    return find_download_shp_from_point(
        point=city_point,
        calculate_point=calculate_point,
        interactive=interactive,
        location_name=f'city "{city}"',
        interactive_callback=region_callback,
    )
