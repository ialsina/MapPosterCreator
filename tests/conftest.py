"""Shared pytest fixtures and utilities for testing."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from ete3 import Tree
from fastapi.testclient import TestClient
from pandas import DataFrame, Series
from shapely.geometry import Point, Polygon

from map_poster_creator.api import app
from map_poster_creator.colorscheme import ColorScheme


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_polygon():
    """Create a sample polygon for testing."""
    return Polygon(
        [
            (-74.006, 40.7128),
            (-73.935, 40.7128),
            (-73.935, 40.7589),
            (-74.006, 40.7589),
            (-74.006, 40.7128),
        ]
    )


@pytest.fixture
def sample_point():
    """Create a sample point for testing."""
    return Point(-73.935, 40.7128)


@pytest.fixture
def sample_coordinates():
    """Sample coordinates for testing."""
    return [
        [-74.006, 40.7128],
        [-73.935, 40.7128],
        [-73.935, 40.7589],
        [-74.006, 40.7589],
    ]


@pytest.fixture
def mock_city_series():
    """Mock city Series for testing."""
    return Series(
        {
            "name": "New York",
            "asciiname": "New York",
            "country code": "US",
            "longitude": -73.935,
            "latitude": 40.7128,
            "population": 8175133,
            "alternatenames": "NYC,New York City",
        }
    )


@pytest.fixture
def mock_city_df(mock_city_series):
    """Mock city DataFrame for testing."""
    return DataFrame([mock_city_series])


@pytest.fixture
def mock_country_df():
    """Mock country DataFrame for testing."""
    return DataFrame(
        [
            {"Name": "United States", "Code": "US"},
            {"Name": "Canada", "Code": "CA"},
        ]
    )


@pytest.fixture
def mock_region_node():
    """Mock region tree node for testing."""
    node = Tree()
    node.name = "north-america/us"
    return node


@pytest.fixture
def mock_geofabrik_urls():
    """Mock GeoFabrik URLs."""
    return {
        "north-america/us": [
            "https://download.geofabrik.de/north-america/us-latest-free.shp.zip"
        ]
    }


@pytest.fixture
def mock_region_polygons(sample_polygon):
    """Mock region polygons."""
    return [sample_polygon]


@pytest.fixture
def mock_region_centroids(sample_point, mock_region_node):
    """Mock region centroids."""
    return {mock_region_node: [sample_point]}


@pytest.fixture
def mock_shp_dir(temp_dir):
    """Create a mock SHP directory with dummy files."""
    shp_dir = temp_dir / "shp"
    shp_dir.mkdir()
    # Create dummy shapefile files
    for filename in [
        "gis_osm_roads_free_1.shp",
        "gis_osm_water_a_free_1.shp",
        "gis_osm_pois_a_free_1.shp",
    ]:
        (shp_dir / filename).touch()
    return shp_dir


@pytest.fixture
def mock_geodataframe():
    """Mock GeoDataFrame for testing."""
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        {
            "fclass": ["primary", "secondary", "footway"],
            "maxspeed": [50, 40, 5],
        },
        geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
        crs="EPSG:4326",
    )
    return gdf


@pytest.fixture
def mock_colorscheme():
    """Mock color scheme for testing."""
    return ColorScheme(
        facecolor="white",
        water="#bdddff",
        greens="#d4ffe1",
        roads="#000000",
    )


@pytest.fixture
def mock_colorschemes(mock_colorscheme):
    """Mock color schemes dictionary."""
    return {
        "white": mock_colorscheme,
        "black": ColorScheme(
            facecolor="black",
            water="#383d52",
            greens="#354038",
            roads="#ffffff",
        ),
    }


@pytest.fixture
def mock_paths(temp_dir):
    """Mock paths configuration."""
    with patch("map_poster_creator.config.paths") as mock_paths:
        mock_paths.output_dir = temp_dir / "output"
        mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
        mock_paths.data_dir = temp_dir / "data"
        mock_paths.data_dir.mkdir(parents=True, exist_ok=True)
        yield mock_paths
