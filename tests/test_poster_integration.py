"""Integration tests that create real poster PNG files.

These tests download real shapefiles from GeoFabrik and may take several minutes.
Run with ``pytest -m integration``. Set KEEP_TEST_OUTPUTS=1 to keep PNG outputs.
"""

import json
import os
from pathlib import Path

import pytest

from map_poster_creator.colorscheme import get_colorscheme
from map_poster_creator.core import create_poster_from_coordinates
from map_poster_creator.data.core import find_download_shp

TEST_WIDTH = 10.0
TEST_DPI = 72

KEEP_OUTPUTS = os.environ.get("KEEP_TEST_OUTPUTS", "0") == "1"
OUTPUT_BASE_DIR = Path(__file__).parent / "test_outputs" if KEEP_OUTPUTS else None


def _assert_valid_png(path: Path, min_size: int = 1000) -> int:
    assert path.exists(), f"Output file was not created: {path}"
    file_size = path.stat().st_size
    assert file_size > 0, f"Output file is empty: {path}"
    with open(path, "rb") as f:
        first_bytes = f.read(8)
    assert first_bytes == b"\x89PNG\r\n\x1a\n", f"Output does not have PNG magic bytes: {path}"
    assert file_size >= min_size, f"Output file seems too small ({file_size} bytes): {path}"
    return file_size


@pytest.fixture(scope="session")
def nyc_coordinates():
    """Load coordinates from tests/data/nyc.json."""
    nyc_json_path = Path(__file__).parent / "data" / "nyc.json"

    with open(nyc_json_path, encoding="utf-8") as f:
        geojson_data = json.load(f)

    geometry_type = geojson_data.get("type")
    coordinates_data = geojson_data.get("coordinates")

    if geometry_type == "MultiPolygon":
        first_polygon_coords = coordinates_data[0][0]
        coordinates = [[float(coord[0]), float(coord[1])] for coord in first_polygon_coords]
    elif geometry_type == "Polygon":
        exterior_coords = coordinates_data[0]
        coordinates = [[float(coord[0]), float(coord[1])] for coord in exterior_coords]
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")

    if len(coordinates) > 1 and coordinates[0] == coordinates[-1]:
        coordinates = coordinates[:-1]

    return coordinates


@pytest.fixture(scope="session")
def nyc_shp_dir():
    """Download real shapefiles from GeoFabrik for New York City."""
    print("\nDownloading real shapefiles from GeoFabrik (this may take a few minutes)...")
    shp_dir = find_download_shp(
        city="New York City",
        country="United States",
        interactive=False,
    )
    print(f"Shapefiles downloaded to: {shp_dir}")

    required_files = [
        "gis_osm_roads_free_1.shp",
        "gis_osm_water_a_free_1.shp",
        "gis_osm_pois_a_free_1.shp",
    ]
    for filename in required_files:
        path = shp_dir / filename
        assert path.exists(), f"Expected shapefile not found: {path}"
        assert path.stat().st_size > 0, f"Shapefile is empty: {path}"

    return shp_dir


@pytest.fixture
def output_dir(temp_dir):
    """Output directory for generated posters."""
    if OUTPUT_BASE_DIR:
        directory = OUTPUT_BASE_DIR
    else:
        directory = temp_dir / "test_outputs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.mark.integration
@pytest.mark.slow
class TestPosterIntegration:
    """Integration tests using real GeoFabrik shapefile downloads."""

    def test_poster_equivalent_to_bash_script(self, output_dir, nyc_coordinates, nyc_shp_dir):
        """Create a real PNG poster equivalent to test_poster.sh."""
        output_file = output_dir / "poster.png"
        color_scheme = get_colorscheme("white")

        create_poster_from_coordinates(
            shp_dir=nyc_shp_dir,
            coordinates=nyc_coordinates,
            color=color_scheme,
            width=TEST_WIDTH,
            dpi=TEST_DPI,
            output=output_file,
        )

        _assert_valid_png(output_file)

    def test_poster_with_different_colors(self, output_dir, nyc_coordinates, nyc_shp_dir):
        """Test creating posters with different color schemes."""
        for color_name in ["white", "black"]:
            try:
                color_scheme = get_colorscheme(color_name)
            except KeyError:
                pytest.skip(f"Color scheme '{color_name}' not available")

            output_file = output_dir / f"poster_{color_name}.png"
            create_poster_from_coordinates(
                shp_dir=nyc_shp_dir,
                coordinates=nyc_coordinates,
                color=color_scheme,
                width=TEST_WIDTH,
                dpi=TEST_DPI,
                output=output_file,
            )
            _assert_valid_png(output_file, min_size=100)

    def test_poster_different_dpi_values(self, output_dir, nyc_coordinates, nyc_shp_dir):
        """Test creating posters with different DPI values."""
        color_scheme = get_colorscheme("white")

        for dpi in [72, 100, 150]:
            output_file = output_dir / f"poster_dpi_{dpi}.png"
            create_poster_from_coordinates(
                shp_dir=nyc_shp_dir,
                coordinates=nyc_coordinates,
                color=color_scheme,
                width=TEST_WIDTH,
                dpi=dpi,
                output=output_file,
            )
            _assert_valid_png(output_file, min_size=100)

    def test_poster_different_widths(self, output_dir, nyc_coordinates, nyc_shp_dir):
        """Test creating posters with different width values."""
        color_scheme = get_colorscheme("white")

        for width in [8.0, 10.0, 12.0]:
            output_file = output_dir / f"poster_width_{width}.png"
            create_poster_from_coordinates(
                shp_dir=nyc_shp_dir,
                coordinates=nyc_coordinates,
                color=color_scheme,
                width=width,
                dpi=TEST_DPI,
                output=output_file,
            )
            _assert_valid_png(output_file, min_size=100)
