#!/usr/bin/env python3
"""
Debug script to create a poster with intermediate visualizations.

This script:
1. Loads coordinates from a JSON file (geometry object)
2. Downloads REAL shapefiles from GeoFabrik
3. Creates intermediate debug visualizations:
   - Boundary superposed on world map
   - Individual layers (roads, water, greens) as black and white images
   - Raw data before preprocessing
4. Creates the final poster image

Usage:
    python examples/debug_poster.py --shape tests/data/panama.json --color black
    python examples/debug_poster.py --shape tests/data/nyc.json --color white
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

# Add parent directory to path so we can import map_poster_creator
sys.path.insert(0, str(Path(__file__).parent.parent))

from shapely.geometry import Point, Polygon, box
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from geopandas import GeoDataFrame
import math
import requests

from map_poster_creator.core import (
    create_poster_from_coordinates,
    shp_filename,
    _preprocessing,
    _preprocessing_roads,
)
from map_poster_creator.colorscheme import get_colorscheme, get_available_colorschemes
from map_poster_creator.data.core import find_download_shp_from_point
from map_poster_creator.geometry import get_map_geometry_from_poly
from map_poster_creator.plotting import plot_dataframe, road_width


def load_coordinates_from_json(json_path: Path):
    """Load coordinates from a JSON file containing a geometry object.

    Args:
        json_path: Path to JSON file containing a Polygon or MultiPolygon geometry

    Returns:
        List of coordinates as [lon, lat] pairs
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Shape file not found: {json_path}")

    # The file contains a geometry object, not a FeatureCollection
    with open(json_path, "r") as f:
        geojson_data = json.load(f)

    geometry_type = geojson_data.get("type")
    coordinates_data = geojson_data.get("coordinates")

    if geometry_type == "MultiPolygon":
        # MultiPolygon: coordinates is a list of polygons, each with coordinate rings
        # Use the first polygon's exterior ring (first ring in first polygon)
        first_polygon_coords = coordinates_data[0][0]  # First polygon, exterior ring
        coordinates = [
            [float(coord[0]), float(coord[1])] for coord in first_polygon_coords
        ]
    elif geometry_type == "Polygon":
        # Polygon: coordinates is a list of rings, first is exterior
        exterior_coords = coordinates_data[0]
        coordinates = [[float(coord[0]), float(coord[1])] for coord in exterior_coords]
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")

    # Remove duplicate last point if it matches first (polygons are often closed)
    if len(coordinates) > 1 and coordinates[0] == coordinates[-1]:
        coordinates = coordinates[:-1]

    return coordinates


_world_map_cache = None


def download_natural_earth_data():
    """Download Natural Earth 110m cultural vectors (countries) data.

    Returns:
        Path to the downloaded shapefile, or None if download fails
    """

    # Try multiple sources for Natural Earth data
    # Source 1: Natural Earth direct (may require redirect)
    # Source 2: GitHub mirror (more reliable)
    NE_URLS = [
        "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip",
        "https://github.com/nvkelso/natural-earth-vector/raw/master/110m_cultural/ne_110m_admin_0_countries.zip",
    ]

    # Cache directory in user's home
    cache_dir = Path.home() / ".mapoc" / "naturalearth"
    cache_dir.mkdir(parents=True, exist_ok=True)

    zip_path = cache_dir / "ne_110m_admin_0_countries.zip"
    shp_path = cache_dir / "ne_110m_admin_0_countries.shp"

    # If already downloaded, return the path
    if shp_path.exists():
        return shp_path

    # Try each URL until one works
    for url in NE_URLS:
        try:
            print(f"  Downloading Natural Earth data from {url.split('/')[-2]}...")
            response = requests.get(url, stream=True, timeout=60, allow_redirects=True)
            response.raise_for_status()

            # Check if we got a valid zip file
            if response.headers.get("content-type", "").startswith("text/html"):
                # Got HTML instead of zip, try next URL
                continue

            with open(zip_path, "wb") as f:
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)

            # Verify it's a valid zip file
            try:
                with zipfile.ZipFile(zip_path, "r") as test_zip:
                    test_zip.testzip()
            except zipfile.BadZipFile:
                # Not a valid zip, try next URL
                zip_path.unlink()
                continue

            # Extract the shapefile
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(cache_dir)

            # Find the .shp file in the extracted contents
            shp_files = list(cache_dir.glob("*.shp"))
            if shp_files:
                return shp_files[0]

            # If no .shp found, try subdirectories
            for subdir in cache_dir.iterdir():
                if subdir.is_dir():
                    shp_files = list(subdir.glob("*.shp"))
                    if shp_files:
                        return shp_files[0]

            # Successfully downloaded but no shapefile found
            break

        except requests.RequestException:
            # Network error, try next URL
            if zip_path.exists():
                zip_path.unlink()
            continue
        except Exception:
            # Other error, try next URL
            if zip_path.exists():
                zip_path.unlink()
            continue

    # All URLs failed
    print("  ⚠ Could not download Natural Earth data automatically.")
    print(
        "  You can manually download from: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/"
    )
    print("  Extract to: ~/.mapoc/naturalearth/")
    return None


def get_world_map_coastlines():
    """Try to get world map coastlines from Natural Earth data.

    Returns:
        GeoDataFrame with world coastlines, or None if not available
    """
    global _world_map_cache
    if _world_map_cache is not None:
        return _world_map_cache

    # Try multiple methods to get Natural Earth data
    world = None

    # Method 1: Try old geopandas.datasets (for older versions)
    try:
        import geopandas.datasets

        world_path = geopandas.datasets.get_path("naturalearth_lowres")
        world = GeoDataFrame.from_file(world_path)
    except (AttributeError, ImportError, Exception):
        pass

    # Method 2: Try to download Natural Earth data automatically
    if world is None:
        try:
            shp_path = download_natural_earth_data()
            if shp_path and shp_path.exists():
                world = GeoDataFrame.from_file(shp_path)
        except Exception:
            pass

    # Method 3: Try to load from common system locations
    if world is None:
        common_paths = [
            Path.home() / ".mapoc" / "naturalearth" / "ne_110m_admin_0_countries.shp",
            Path("/usr/share/naturalearth/ne_110m_admin_0_countries.shp"),
            Path("/usr/local/share/naturalearth/ne_110m_admin_0_countries.shp"),
        ]
        for path in common_paths:
            if path.exists():
                try:
                    world = GeoDataFrame.from_file(path)
                    break
                except Exception:
                    continue

    # If we got data, ensure CRS is set and cache it
    if world is not None and not world.empty:
        # Ensure CRS is set
        if world.crs is None:
            world.set_crs("EPSG:4326", inplace=True)
        elif str(world.crs) != "EPSG:4326":
            world = world.to_crs("EPSG:4326")
        _world_map_cache = world
        return world

    # If all methods failed, return None
    return None


def plot_boundary_at_zoom_level(
    polygon: Polygon,
    ax: Axes,
    bounds: tuple,
    title: str,
    show_coastlines: bool = True,
    show_grid: bool = True,
):
    """Plot boundary polygon at a specific zoom level.

    Args:
        polygon: The boundary polygon to plot
        ax: Matplotlib axes to plot on
        bounds: (left, bottom, right, top) bounds for the map
        title: Title for the subplot
        show_coastlines: Whether to show world map coastlines
        show_grid: Whether to show grid lines
    """
    left, bottom, right, top = bounds

    # Set map bounds
    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)

    # Calculate aspect ratio based on latitude
    center_lat = (top + bottom) / 2
    if math.isfinite(center_lat) and -90 <= center_lat <= 90:
        cos_lat = math.cos(math.pi / 180 * center_lat)
        if cos_lat > 0 and math.isfinite(cos_lat):
            aspect_ratio = 1 / cos_lat
        else:
            aspect_ratio = 1.0
    else:
        aspect_ratio = 1.0
    ax.set_aspect(aspect_ratio)

    # Try to plot world map coastlines (plot FIRST so it's behind everything)
    if show_coastlines:
        world_gdf = get_world_map_coastlines()
        if world_gdf is not None and not world_gdf.empty:
            try:
                # Ensure CRS is set correctly
                if world_gdf.crs is None:
                    world_gdf.set_crs("EPSG:4326", inplace=True)
                elif str(world_gdf.crs) != "EPSG:4326":
                    world_gdf = world_gdf.to_crs("EPSG:4326")

                # Try to clip world map to visible bounds with buffer for performance
                buffer = max((right - left) * 0.2, (top - bottom) * 0.2, 2.0)
                clip_left = max(left - buffer, -180)
                clip_right = min(right + buffer, 180)
                clip_bottom = max(bottom - buffer, -90)
                clip_top = min(top + buffer, 90)

                # Use spatial indexing for better performance
                try:
                    world_clipped = world_gdf.cx[
                        clip_left:clip_right, clip_bottom:clip_top
                    ]
                    if not world_clipped.empty:
                        # Plot clipped version
                        world_clipped.plot(
                            ax=ax,
                            color="lightblue",
                            edgecolor="darkblue",
                            linewidth=0.8,
                            alpha=0.5,
                            zorder=1,
                        )
                    else:
                        # If clipping results in empty, plot all
                        world_gdf.plot(
                            ax=ax,
                            color="lightblue",
                            edgecolor="darkblue",
                            linewidth=0.8,
                            alpha=0.5,
                            zorder=1,
                        )
                except (KeyError, ValueError, AttributeError):
                    # If cx indexing fails, plot all (might be slower but will work)
                    world_gdf.plot(
                        ax=ax,
                        color="lightblue",
                        edgecolor="darkblue",
                        linewidth=0.8,
                        alpha=0.5,
                        zorder=1,
                    )
            except Exception:
                # If plotting fails, try one more time with all data
                try:
                    if world_gdf.crs is None:
                        world_gdf.set_crs("EPSG:4326", inplace=True)
                    elif str(world_gdf.crs) != "EPSG:4326":
                        world_gdf = world_gdf.to_crs("EPSG:4326")
                    world_gdf.plot(
                        ax=ax,
                        color="lightblue",
                        edgecolor="darkblue",
                        linewidth=0.8,
                        alpha=0.5,
                        zorder=1,
                    )
                except Exception:
                    # If all fails, print warning but continue
                    pass  # Silently fail - world map is optional

    # Draw grid lines if requested
    if show_grid:
        # Calculate appropriate grid spacing based on zoom level
        lon_range = right - left
        lat_range = top - bottom

        if lon_range > 100:  # World view
            lon_step, lat_step = 30, 30
        elif lon_range > 20:  # Regional view
            lon_step, lat_step = 5, 5
        elif lon_range > 5:  # Country view
            lon_step, lat_step = 1, 1
        else:  # Local view
            lon_step, lat_step = 0.5, 0.5

        # Draw latitude lines (handle float steps properly)
        lat_start = math.floor(bottom / lat_step) * lat_step
        lat = lat_start
        while lat <= top:
            if bottom <= lat <= top:
                ax.axhline(
                    y=lat, color="lightgray", linestyle="--", linewidth=0.3, alpha=0.5
                )
            lat += lat_step

        # Draw longitude lines (handle float steps properly)
        lon_start = math.floor(left / lon_step) * lon_step
        lon = lon_start
        while lon <= right:
            if left <= lon <= right:
                ax.axvline(
                    x=lon, color="lightgray", linestyle="--", linewidth=0.3, alpha=0.5
                )
            lon += lon_step

        # Draw equator and prime meridian more prominently if visible
        if bottom <= 0 <= top:
            ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.8, alpha=0.7)
        if left <= 0 <= right:
            ax.axvline(x=0, color="gray", linestyle="-", linewidth=0.8, alpha=0.7)

    # Plot the boundary polygon (above world map)
    # Always plot the boundary, even if it extends beyond the view bounds
    gdf_polygon = GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")

    # Check if polygon intersects with the view bounds
    view_box = box(left, bottom, right, top)
    polygon_intersects = polygon.intersects(view_box)

    if polygon_intersects:
        # Plot the polygon - it will be clipped to view bounds automatically
        # Use thicker line for better visibility
        linewidth = (
            3.0
            if "Regional" in title or "Local" in title or "Boundary" in title
            else 2.5
        )
        gdf_polygon.plot(
            ax=ax,
            color="red",
            edgecolor="darkred",
            linewidth=linewidth,
            alpha=0.8,
            zorder=5,
        )

        # Also plot the intersection explicitly to ensure visibility
        try:
            intersection = polygon.intersection(view_box)
            if not intersection.is_empty:
                gdf_intersection = GeoDataFrame(
                    [1], geometry=[intersection], crs="EPSG:4326"
                )
                gdf_intersection.plot(
                    ax=ax,
                    color="red",
                    edgecolor="darkred",
                    linewidth=linewidth,
                    alpha=0.9,
                    zorder=6,
                )
        except Exception:
            # If intersection fails, the original plot should still work
            pass

    # Add centroid marker
    centroid = polygon.centroid
    if left <= centroid.x <= right and bottom <= centroid.y <= top:
        ax.plot(
            centroid.x,
            centroid.y,
            "ro",
            markersize=10,
            label="Centroid",
            zorder=10,
            markeredgecolor="darkred",
            markeredgewidth=2,
        )
        ax.legend(loc="upper right", fontsize=8)
    elif polygon_intersects:
        # Even if centroid is outside, show it if polygon is visible
        # Project centroid to nearest edge if outside bounds
        plot_x = max(left, min(centroid.x, right))
        plot_y = max(bottom, min(centroid.y, top))
        ax.plot(
            plot_x,
            plot_y,
            "ro",
            markersize=8,
            label="Centroid (approx)",
            zorder=10,
            markeredgecolor="darkred",
            markeredgewidth=1,
            alpha=0.7,
        )
        ax.legend(loc="upper right", fontsize=8)

    # Add title
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.grid(True, alpha=0.2)

    # Add bounds text
    bounds_text = f"[{left:.2f}, {bottom:.2f}, {right:.2f}, {top:.2f}]"
    ax.text(
        0.02,
        0.98,
        bounds_text,
        transform=ax.transAxes,
        fontsize=8,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7),
    )


def plot_boundary_on_world_map(polygon: Polygon, output_path: Path, dpi: int = 150):
    """Plot the boundary polygon superposed on world map at various zoom levels.

    Args:
        polygon: The boundary polygon to plot
        output_path: Path to save the visualization
        dpi: DPI for the output image
    """
    bounds = polygon.bounds
    left, bottom, right, top = bounds

    # Calculate zoom levels
    lon_center = (left + right) / 2
    lat_center = (bottom + top) / 2
    lon_range = right - left
    lat_range = top - bottom

    # Define zoom levels with different bounds
    # Ensure minimum range to avoid invalid bounds
    min_lon_range = max(lon_range, 0.1)
    min_lat_range = max(lat_range, 0.1)

    zoom_levels = [
        {"name": "World View", "bounds": (-180, -90, 180, 90), "figsize": (16, 8)},
        {
            "name": "Hemisphere View",
            "bounds": (
                max(lon_center - 90, -180),
                max(lat_center - 45, -90),
                min(lon_center + 90, 180),
                min(lat_center + 45, 90),
            ),
            "figsize": (12, 8),
        },
        {
            "name": "Regional View",
            "bounds": (
                lon_center - max(min_lon_range * 5, 10),
                lat_center - max(min_lat_range * 5, 10),
                lon_center + max(min_lon_range * 5, 10),
                lat_center + max(min_lat_range * 5, 10),
            ),
            "figsize": (12, 10),
        },
        {
            "name": "Local View",
            "bounds": (
                lon_center - max(min_lon_range * 1.5, 1),
                lat_center - max(min_lat_range * 1.5, 1),
                lon_center + max(min_lon_range * 1.5, 1),
                lat_center + max(min_lat_range * 1.5, 1),
            ),
            "figsize": (12, 10),
        },
        {
            "name": "Boundary View",
            "bounds": (
                left - min_lon_range * 0.1,
                bottom - min_lat_range * 0.1,
                right + min_lon_range * 0.1,
                top + min_lat_range * 0.1,
            ),
            "figsize": (12, 10),
        },
    ]

    # Create a figure with all zoom levels
    fig = plt.figure(figsize=(20, 16), facecolor="white")
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    axes = [
        fig.add_subplot(gs[0, :]),  # World view (full width)
        fig.add_subplot(gs[1, 0]),  # Hemisphere view
        fig.add_subplot(gs[1, 1]),  # Regional view
        fig.add_subplot(gs[2, 0]),  # Local view
        fig.add_subplot(gs[2, 1]),  # Boundary view
    ]

    # Validate bounds and filter out invalid zoom levels
    valid_zoom_levels = []
    valid_axes = []
    for i, zoom in enumerate(zoom_levels):
        z_left, z_bottom, z_right, z_top = zoom["bounds"]
        if z_right > z_left and z_top > z_bottom:
            valid_zoom_levels.append(zoom)
            valid_axes.append(axes[i])

    if not valid_zoom_levels:
        # Fallback: use world view only
        valid_zoom_levels = [zoom_levels[0]]
        valid_axes = [axes[0]]

    # Plot each valid zoom level
    for i, zoom in enumerate(valid_zoom_levels):
        try:
            plot_boundary_at_zoom_level(
                polygon=polygon,
                ax=valid_axes[i],
                bounds=zoom["bounds"],
                title=zoom["name"],
                show_coastlines=True,
                show_grid=True,
            )
        except Exception as e:
            # If plotting fails for a zoom level, show error message
            valid_axes[i].text(
                0.5,
                0.5,
                f"Error plotting {zoom['name']}:\n{str(e)}",
                transform=valid_axes[i].transAxes,
                ha="center",
                va="center",
                fontsize=10,
                bbox=dict(boxstyle="round", facecolor="red", alpha=0.3),
            )
            valid_axes[i].set_title(zoom["name"], fontsize=11, fontweight="bold")

    # Add overall title
    fig.suptitle(
        "Boundary Polygon at Various Zoom Levels",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"  ✓ World map visualization saved: {output_path}")


def plot_layer_black_white(
    gdf: GeoDataFrame,
    geometry,
    layer_name: str,
    output_path: Path,
    dpi: int = 300,
    width: float = 15.0,
    linewidth: float = 0.1,
    linewidths: list = None,
):
    """Plot a single layer as a black and white image.

    Args:
        gdf: GeoDataFrame to plot
        geometry: MapGeometry object with bounds
        layer_name: Name of the layer (for title)
        output_path: Path to save the visualization
        dpi: DPI for the output image
        width: Width of the figure in inches
        linewidth: Line width for plotting (if linewidths not provided)
        linewidths: List of line widths (for roads with different speeds)
    """
    if gdf.empty:
        print(f"  ⚠ Layer '{layer_name}' is empty, skipping visualization")
        return

    plt.clf()
    fig, ax = plt.subplots(figsize=(width, width), facecolor="white")

    if not isinstance(ax, Axes):
        return

    # Set limits and aspect ratio
    if (
        math.isfinite(geometry.bottom)
        and math.isfinite(geometry.top)
        and geometry.top > geometry.bottom
    ):
        ax.set_ylim((geometry.bottom, geometry.top))
    else:
        print(f"  ⚠ Invalid y-axis bounds for {layer_name}, skipping")
        plt.close()
        return

    if (
        math.isfinite(geometry.left)
        and math.isfinite(geometry.right)
        and geometry.right > geometry.left
    ):
        ax.set_xlim((geometry.left, geometry.right))
    else:
        print(f"  ⚠ Invalid x-axis bounds for {layer_name}, skipping")
        plt.close()
        return

    # Set aspect ratio according to latitude
    try:
        latitude = geometry.center[0]
        if math.isfinite(latitude) and -90 <= latitude <= 90:
            cos_lat = math.cos(math.pi / 180 * latitude)
            if cos_lat > 0 and math.isfinite(cos_lat):
                aspect_ratio = 1 / cos_lat
            else:
                aspect_ratio = 1.0
        else:
            aspect_ratio = 1.0
        ax.set_aspect(aspect_ratio)
    except (ValueError, ZeroDivisionError, OverflowError):
        ax.set_aspect(1.0)

    # Plot the layer in black
    try:
        if linewidths is not None:
            plot_dataframe(ax=ax, gdf=gdf, color="black", linewidth=linewidths)
        else:
            plot_dataframe(ax=ax, gdf=gdf, color="black", lw=linewidth)
    except Exception as e:
        print(f"  ⚠ Error plotting {layer_name}: {e}")
        plt.close()
        return

    ax.set_axis_off()
    ax.set_title(
        f"{layer_name.capitalize()} Layer (Black & White)",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    # Add info text
    info_text = f"Features: {len(gdf)}"
    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.savefig(output_path, bbox_inches="tight", dpi=dpi)
    plt.close()
    print(f"  ✓ {layer_name.capitalize()} layer visualization saved: {output_path}")


def plot_raw_data(
    shp_dir: Path,
    polygon: Polygon,
    geometry,
    output_dir: Path,
    dpi: int = 300,
    width: float = 15.0,
):
    """Plot raw shapefile data before preprocessing.

    Args:
        shp_dir: Directory containing shapefiles
        polygon: Boundary polygon
        geometry: MapGeometry object
        output_dir: Directory to save visualizations
        dpi: DPI for output images
        width: Width of figures in inches
    """
    print("\n  Creating raw data visualizations (before preprocessing)...")

    # Load raw data
    try:
        raw_roads = GeoDataFrame.from_file(
            shp_dir / shp_filename.roads, encoding="utf-8"
        )
        # Clip to approximate bounds (for performance)
        bounds = polygon.bounds
        buffer = 0.1  # Small buffer
        raw_roads_clipped = raw_roads.cx[
            bounds[0] - buffer : bounds[2] + buffer,
            bounds[1] - buffer : bounds[3] + buffer,
        ]
        plot_layer_black_white(
            raw_roads_clipped,
            geometry,
            "raw_roads",
            output_dir / "debug_raw_roads.png",
            dpi=dpi,
            width=width,
            linewidth=0.05,
        )
    except Exception as e:
        print(f"  ⚠ Could not visualize raw roads: {e}")

    try:
        raw_water = GeoDataFrame.from_file(
            shp_dir / shp_filename.water, encoding="utf-8"
        )
        bounds = polygon.bounds
        buffer = 0.1
        raw_water_clipped = raw_water.cx[
            bounds[0] - buffer : bounds[2] + buffer,
            bounds[1] - buffer : bounds[3] + buffer,
        ]
        plot_layer_black_white(
            raw_water_clipped,
            geometry,
            "raw_water",
            output_dir / "debug_raw_water.png",
            dpi=dpi,
            width=width,
            linewidth=0.1,
        )
    except Exception as e:
        print(f"  ⚠ Could not visualize raw water: {e}")

    try:
        raw_greens = GeoDataFrame.from_file(
            shp_dir / shp_filename.greens, encoding="utf-8"
        )
        bounds = polygon.bounds
        buffer = 0.1
        raw_greens_clipped = raw_greens.cx[
            bounds[0] - buffer : bounds[2] + buffer,
            bounds[1] - buffer : bounds[3] + buffer,
        ]
        plot_layer_black_white(
            raw_greens_clipped,
            geometry,
            "raw_greens",
            output_dir / "debug_raw_greens.png",
            dpi=dpi,
            width=width,
            linewidth=0.1,
        )
    except Exception as e:
        print(f"  ⚠ Could not visualize raw greens: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a map poster with debug visualizations from a shape file (JSON geometry)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --shape tests/data/panama.json --color black
  %(prog)s --shape tests/data/nyc.json --color white
  %(prog)s --shape tests/data/tokyo.json --color black
        """,
    )

    parser.add_argument(
        "--shape",
        type=Path,
        required=True,
        help="Path to JSON file containing a Polygon or MultiPolygon geometry",
    )

    parser.add_argument(
        "--color",
        type=str,
        default="white",
        help=f"Color scheme name (default: white). Available: {', '.join(get_available_colorschemes())}",
    )

    parser.add_argument(
        "--debug-dir",
        type=Path,
        default=None,
        help="Directory to save debug visualizations (default: same as output directory)",
    )

    return parser.parse_args()


def main():
    """Main function to create poster with debug visualizations from shape coordinates."""
    args = parse_arguments()

    shape_path = args.shape
    color_name = args.color

    print(f"Creating poster with debug visualizations from shape file: {shape_path}")
    print(f"Using color scheme: {color_name}")

    # Validate color scheme
    available_colors = get_available_colorschemes()
    if color_name not in available_colors:
        print(f"\n✗ Error: Color scheme '{color_name}' not available.")
        print(f"  Available color schemes: {', '.join(available_colors)}")
        return 1

    # Load coordinates from JSON file
    print(f"\nLoading coordinates from {shape_path}...")
    try:
        coordinates = load_coordinates_from_json(shape_path)
        print(f"Loaded {len(coordinates)} coordinate points")
    except Exception as e:
        print(f"\n✗ Error loading coordinates: {e}")
        return 1

    # Create polygon and get geometry
    polygon = Polygon(coordinates)
    geometry = get_map_geometry_from_poly(polygon)
    centroid = polygon.centroid
    centroid_point = Point(centroid.x, centroid.y)
    print(f"Polygon centroid: ({centroid.x:.6f}, {centroid.y:.6f})")
    print(
        f"Polygon bounds: [{geometry.left:.6f}, {geometry.bottom:.6f}, {geometry.right:.6f}, {geometry.top:.6f}]"
    )

    # Download REAL shapefiles from GeoFabrik
    print(
        "\nDownloading real shapefiles from GeoFabrik (this may take a few minutes)..."
    )
    try:
        shp_dir = find_download_shp_from_point(
            point=centroid_point,
            calculate_point=True,
            interactive=False,
            location_name=f"area from {shape_path.stem}",
        )
        print(f"Shapefiles downloaded to: {shp_dir}")
    except Exception as e:
        print(f"\n✗ Error downloading shapefiles: {e}")
        return 1

    # Get color scheme
    try:
        color_scheme = get_colorscheme(color_name)
    except KeyError:
        print(f"\n✗ Error: Color scheme '{color_name}' not found.")
        return 1

    # Create output directory
    shape_name = shape_path.stem
    output_dir = Path(__file__).parent / "output"
    if args.debug_dir:
        debug_dir = Path(args.debug_dir)
    else:
        debug_dir = output_dir / f"{shape_name}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    # Create debug visualizations
    print("\n" + "=" * 60)
    print("Creating debug visualizations...")
    print("=" * 60)

    # 1. Boundary on world map
    print("\n1. Creating boundary on world map visualization...")
    try:
        plot_boundary_on_world_map(
            polygon, debug_dir / "debug_boundary_world_map.png", dpi=150
        )
    except Exception as e:
        print(f"  ✗ Error creating world map visualization: {e}")
        import traceback

        traceback.print_exc()

    # 2. Raw data visualizations
    try:
        plot_raw_data(shp_dir, polygon, geometry, debug_dir, dpi=300, width=15.0)
    except Exception as e:
        print(f"  ✗ Error creating raw data visualizations: {e}")
        import traceback

        traceback.print_exc()

    # 3. Preprocess data and create layer visualizations
    print("\n3. Creating processed layer visualizations...")
    try:
        # Preprocess each layer
        roads = _preprocessing_roads(
            poly=polygon,
            gdf=GeoDataFrame.from_file(shp_dir / shp_filename.roads, encoding="utf-8"),
        )
        water = _preprocessing(
            poly=polygon,
            gdf=GeoDataFrame.from_file(shp_dir / shp_filename.water, encoding="utf-8"),
        )
        greens = _preprocessing(
            poly=polygon,
            gdf=GeoDataFrame.from_file(shp_dir / shp_filename.greens, encoding="utf-8"),
        )

        # Plot each processed layer
        road_linewidths = (
            [road_width(d) for d in roads.speeds]
            if not roads.empty and "speeds" in roads.columns
            else None
        )

        plot_layer_black_white(
            roads,
            geometry,
            "roads",
            debug_dir / "debug_layer_roads.png",
            dpi=300,
            width=15.0,
            linewidths=road_linewidths,
        )

        plot_layer_black_white(
            water,
            geometry,
            "water",
            debug_dir / "debug_layer_water.png",
            dpi=300,
            width=15.0,
            linewidth=0.1,
        )

        plot_layer_black_white(
            greens,
            geometry,
            "greens",
            debug_dir / "debug_layer_greens.png",
            dpi=300,
            width=15.0,
            linewidth=0.1,
        )

        # Print statistics
        print("\n  Layer statistics:")
        print(f"    Roads: {len(roads)} features")
        print(f"    Water: {len(water)} features")
        print(f"    Greens: {len(greens)} features")

    except Exception as e:
        print(f"  ✗ Error creating processed layer visualizations: {e}")
        import traceback

        traceback.print_exc()

    # 4. Create the final poster
    print("\n" + "=" * 60)
    print("Creating final poster...")
    print("=" * 60)

    output_file = output_dir / f"poster_{shape_name}_{color_name}.png"

    try:
        create_poster_from_coordinates(
            shp_dir=shp_dir,
            coordinates=coordinates,
            color=color_scheme,
            width=15.0,
            dpi=300,
            output=output_file,
        )
    except Exception as e:
        print(f"\n✗ Error creating poster: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Verify output
    if output_file.exists():
        file_size = output_file.stat().st_size
        print("\n✓ Poster created successfully!")
        print(f"  Output file: {output_file}")
        print(f"  File size: {file_size:,} bytes")

        # Verify PNG format
        with open(output_file, "rb") as f:
            first_bytes = f.read(8)
            if first_bytes == b"\x89PNG\r\n\x1a\n":
                print("  Format: Valid PNG image")
            else:
                print("  Warning: File may not be a valid PNG")
    else:
        print("\n✗ Error: Output file was not created")
        return 1

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Final poster: {output_file}")
    print(f"  Debug visualizations: {debug_dir}")
    print("    - Boundary on world map: debug_boundary_world_map.png")
    print("    - Raw roads: debug_raw_roads.png")
    print("    - Raw water: debug_raw_water.png")
    print("    - Raw greens: debug_raw_greens.png")
    print("    - Processed roads layer: debug_layer_roads.png")
    print("    - Processed water layer: debug_layer_water.png")
    print("    - Processed greens layer: debug_layer_greens.png")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
