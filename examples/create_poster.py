#!/usr/bin/env python3
"""
Simple example script to create a poster from any shape coordinates.

This script:
1. Loads coordinates from a JSON file (geometry object)
2. Downloads REAL shapefiles from GeoFabrik
3. Creates a poster image with the specified color scheme

Usage:
    python examples/create_poster.py --shape tests/data/panama.json --color black
    python examples/create_poster.py --shape tests/data/nyc.json --color white
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path so we can import map_poster_creator
sys.path.insert(0, str(Path(__file__).parent.parent))

from shapely.geometry import Point, Polygon

from map_poster_creator.colorscheme import get_available_colorschemes, get_colorscheme
from map_poster_creator.core import create_poster_from_coordinates
from map_poster_creator.data.core import find_download_shp_from_point


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
    with open(json_path) as f:
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a map poster from a shape file (JSON geometry)",
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

    return parser.parse_args()


def main():
    """Main function to create poster from shape coordinates."""
    args = parse_arguments()

    shape_path = args.shape
    color_name = args.color

    print(f"Creating poster from shape file: {shape_path}")
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

    # Calculate centroid for finding SHP files
    polygon = Polygon(coordinates)
    centroid = polygon.centroid
    centroid_point = Point(centroid.x, centroid.y)
    print(f"Polygon centroid: ({centroid.x:.6f}, {centroid.y:.6f})")

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

    # Create output file (based on input shape name and color)
    shape_name = shape_path.stem
    output_file = (
        Path(__file__).parent / "output" / f"poster_{shape_name}_{color_name}.png"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create the poster
    print("\nCreating poster...")
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
