"""Integration test equivalent to test_poster.sh that creates a real image.

This test calls the Python API directly and creates an actual PNG image file,
equivalent to what the bash script test_poster.sh does via the HTTP API.

This test downloads REAL shapefiles from GeoFabrik and uses REAL data.
It may take several minutes to run as it downloads actual map data.

Output files are saved to tests/test_outputs/ by default (same as bash script).
Set KEEP_TEST_OUTPUTS=1 environment variable to keep files after test completion.
"""

import json
import os
from pathlib import Path
import pytest
from shapely.geometry import Point

from map_poster_creator.core import create_poster_from_coordinates
from map_poster_creator.colorscheme import get_colorscheme
from map_poster_creator.data.core import find_download_shp_from_point

# Use persistent output directory (same as bash script) or temp if not keeping outputs
KEEP_OUTPUTS = os.environ.get("KEEP_TEST_OUTPUTS", "0") == "1"
if KEEP_OUTPUTS:
    # Use persistent directory in tests/test_outputs (same as bash script)
    OUTPUT_BASE_DIR = Path(__file__).parent / "test_outputs"
else:
    # Use temp directory that will be cleaned up
    OUTPUT_BASE_DIR = None


class TestPosterIntegration:
    """Integration tests that create real image files using real downloaded data."""

    @pytest.fixture
    def nyc_coordinates(self):
        """Load coordinates from tests/data/nyc.json."""
        nyc_json_path = Path(__file__).parent / "data" / "nyc.json"

        # The file contains a geometry object, not a FeatureCollection
        # Parse it directly
        with open(nyc_json_path, "r") as f:
            geojson_data = json.load(f)

        geometry_type = geojson_data.get("type")
        coordinates_data = geojson_data.get("coordinates")

        if geometry_type == "MultiPolygon":
            # MultiPolygon: coordinates is a list of polygons, each with coordinate rings
            # Use the first polygon's exterior ring (first ring in first polygon)
            first_polygon_coords = coordinates_data[0][
                0
            ]  # First polygon, exterior ring
            coordinates = [
                [float(coord[0]), float(coord[1])] for coord in first_polygon_coords
            ]
        elif geometry_type == "Polygon":
            # Polygon: coordinates is a list of rings, first is exterior
            exterior_coords = coordinates_data[0]
            coordinates = [
                [float(coord[0]), float(coord[1])] for coord in exterior_coords
            ]
        else:
            raise ValueError(f"Unsupported geometry type: {geometry_type}")

        # Remove duplicate last point if it matches first (polygons are often closed)
        if len(coordinates) > 1 and coordinates[0] == coordinates[-1]:
            coordinates = coordinates[:-1]

        return coordinates

    @pytest.fixture
    def nyc_centroid(self, nyc_coordinates):
        """Calculate centroid from NYC coordinates."""
        from shapely.geometry import Polygon

        polygon = Polygon(nyc_coordinates)
        centroid = polygon.centroid
        return Point(centroid.x, centroid.y)

    def test_poster_equivalent_to_bash_script(
        self, temp_dir, nyc_coordinates, nyc_centroid
    ):
        """
        Test equivalent to test_poster.sh that creates a real PNG image.

        This test:
        1. Uses coordinates from tests/data/nyc.json
        2. Downloads REAL shapefiles from GeoFabrik
        3. Calls create_poster_from_coordinates directly (not mocked)
        4. Validates the output PNG file was created correctly

        Output is saved to tests/test_outputs/poster.png (same as bash script)
        if KEEP_TEST_OUTPUTS=1 is set, otherwise uses a temporary directory.
        """
        # Use persistent output directory if KEEP_TEST_OUTPUTS is set, otherwise use temp
        if OUTPUT_BASE_DIR:
            output_dir = OUTPUT_BASE_DIR
        else:
            output_dir = temp_dir / "test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download REAL shapefiles for the test area (New York coordinates)
        # This will download actual OpenStreetMap data from GeoFabrik
        print(
            "\nDownloading real shapefiles from GeoFabrik (this may take a few minutes)..."
        )
        shp_dir = find_download_shp_from_point(
            point=nyc_centroid,
            calculate_point=True,
            interactive=False,
            location_name="test area",
        )
        print(f"Shapefiles downloaded to: {shp_dir}")

        # Output file (equivalent to test_outputs/poster.png)
        output_file = output_dir / "poster.png"

        # Get color scheme (default "white" as in bash script)
        color_scheme = get_colorscheme("white")

        # Call create_poster_from_coordinates directly (equivalent to POST /poster/simple)
        # This uses REAL downloaded shapefiles
        print("Creating poster with real data...")
        create_poster_from_coordinates(
            shp_dir=shp_dir,
            coordinates=nyc_coordinates,
            color=color_scheme,
            width=15.0,
            dpi=300,
            output=output_file,
        )

        # Verify output file exists (equivalent to checking file creation in bash)
        assert output_file.exists(), "Output file was not created"

        # Verify file size is not zero (equivalent to FILE_SIZE check)
        file_size = output_file.stat().st_size
        assert file_size > 0, f"Output file is empty (size: {file_size} bytes)"

        # Verify PNG magic bytes (equivalent to PNG validation in bash)
        with open(output_file, "rb") as f:
            first_bytes = f.read(8)
            # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
            expected_magic = b"\x89PNG\r\n\x1a\n"
            assert first_bytes == expected_magic, (
                f"Output does not have PNG magic bytes. "
                f"Got: {first_bytes.hex()}, Expected: {expected_magic.hex()}"
            )

        # Additional validation: check file is reasonably sized (not just header)
        # A real poster should be at least a few KB
        assert file_size > 1000, (
            f"Output file seems too small (size: {file_size} bytes)"
        )

        # Print output location for user reference
        print(f"\n✓ Poster created successfully at: {output_file}")
        if OUTPUT_BASE_DIR:
            print(f"  Output directory: {output_dir} (persistent - files will be kept)")
        else:
            print(f"  Output directory: {output_dir} (temporary - will be cleaned up)")
            print("  Set KEEP_TEST_OUTPUTS=1 to save files to tests/test_outputs/")

    def test_poster_with_different_colors(
        self, temp_dir, nyc_coordinates, nyc_centroid
    ):
        """Test creating posters with different color schemes using real data."""
        # Use persistent output directory if KEEP_TEST_OUTPUTS is set, otherwise use temp
        if OUTPUT_BASE_DIR:
            output_dir = OUTPUT_BASE_DIR
        else:
            output_dir = temp_dir / "test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download REAL shapefiles for the test area (New York coordinates)
        print(
            "\nDownloading real shapefiles from GeoFabrik (this may take a few minutes)..."
        )
        shp_dir = find_download_shp_from_point(
            point=nyc_centroid,
            calculate_point=True,
            interactive=False,
            location_name="test area",
        )
        print(f"Shapefiles downloaded to: {shp_dir}")

        # Test with different color schemes (equivalent to COLOR environment variable)
        color_schemes = ["white", "black"]

        for color_name in color_schemes:
            try:
                color_scheme = get_colorscheme(color_name)
            except KeyError:
                pytest.skip(f"Color scheme '{color_name}' not available")

            output_file = output_dir / f"poster_{color_name}.png"

            print(f"Creating poster with {color_name} color scheme...")
            create_poster_from_coordinates(
                shp_dir=shp_dir,
                coordinates=nyc_coordinates,
                color=color_scheme,
                width=15.0,
                dpi=300,
                output=output_file,
            )

            # Verify file was created and is valid
            assert output_file.exists(), f"Output file for {color_name} was not created"
            assert output_file.stat().st_size > 0, (
                f"Output file for {color_name} is empty"
            )

            # Verify PNG magic bytes
            with open(output_file, "rb") as f:
                first_bytes = f.read(8)
                assert first_bytes == b"\x89PNG\r\n\x1a\n", (
                    f"Output for {color_name} does not have PNG magic bytes"
                )

    def test_poster_different_dpi_values(self, temp_dir, nyc_coordinates, nyc_centroid):
        """Test creating posters with different DPI values using real data."""
        # Use persistent output directory if KEEP_TEST_OUTPUTS is set, otherwise use temp
        if OUTPUT_BASE_DIR:
            output_dir = OUTPUT_BASE_DIR
        else:
            output_dir = temp_dir / "test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download REAL shapefiles for the test area (New York coordinates)
        print(
            "\nDownloading real shapefiles from GeoFabrik (this may take a few minutes)..."
        )
        shp_dir = find_download_shp_from_point(
            point=nyc_centroid,
            calculate_point=True,
            interactive=False,
            location_name="test area",
        )
        print(f"Shapefiles downloaded to: {shp_dir}")

        color_scheme = get_colorscheme("white")

        # Test different DPI values
        for dpi in [150, 300, 600]:
            output_file = output_dir / f"poster_dpi_{dpi}.png"

            print(f"Creating poster with DPI {dpi}...")
            create_poster_from_coordinates(
                shp_dir=shp_dir,
                coordinates=nyc_coordinates,
                color=color_scheme,
                width=15.0,
                dpi=dpi,
                output=output_file,
            )

            # Verify file was created
            assert output_file.exists(), f"Output file for DPI {dpi} was not created"
            assert output_file.stat().st_size > 0, f"Output file for DPI {dpi} is empty"

            # Verify PNG format
            with open(output_file, "rb") as f:
                first_bytes = f.read(8)
                assert first_bytes == b"\x89PNG\r\n\x1a\n"

    def test_poster_different_widths(self, temp_dir, nyc_coordinates, nyc_centroid):
        """Test creating posters with different width values using real data."""
        # Use persistent output directory if KEEP_TEST_OUTPUTS is set, otherwise use temp
        if OUTPUT_BASE_DIR:
            output_dir = OUTPUT_BASE_DIR
        else:
            output_dir = temp_dir / "test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download REAL shapefiles for the test area (New York coordinates)
        print(
            "\nDownloading real shapefiles from GeoFabrik (this may take a few minutes)..."
        )
        shp_dir = find_download_shp_from_point(
            point=nyc_centroid,
            calculate_point=True,
            interactive=False,
            location_name="test area",
        )
        print(f"Shapefiles downloaded to: {shp_dir}")

        color_scheme = get_colorscheme("white")

        # Test different width values
        for width in [10.0, 15.0, 20.0]:
            output_file = output_dir / f"poster_width_{width}.png"

            print(f"Creating poster with width {width}...")
            create_poster_from_coordinates(
                shp_dir=shp_dir,
                coordinates=nyc_coordinates,
                color=color_scheme,
                width=width,
                dpi=300,
                output=output_file,
            )

            # Verify file was created
            assert output_file.exists(), (
                f"Output file for width {width} was not created"
            )
            assert output_file.stat().st_size > 0, (
                f"Output file for width {width} is empty"
            )

            # Verify PNG format
            with open(output_file, "rb") as f:
                first_bytes = f.read(8)
                assert first_bytes == b"\x89PNG\r\n\x1a\n"
