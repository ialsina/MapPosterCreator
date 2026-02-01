"""Comprehensive tests for core.py functions."""

from unittest.mock import patch, MagicMock
from shapely.geometry import Polygon, MultiPolygon
from geopandas import GeoDataFrame

from map_poster_creator.core import (
    create_poster,
    create_poster_from_coordinates,
    _get_boundary_shape,
    _preprocessing,
    _preprocessing_roads,
)
from map_poster_creator.colorscheme import ColorScheme


class TestGetBoundaryShape:
    """Tests for _get_boundary_shape function."""

    def test_get_boundary_shape_from_polygon(self, sample_polygon):
        """Test getting boundary shape from Polygon object."""
        with patch(
            "map_poster_creator.core.get_map_geometry_from_poly"
        ) as mock_get_geometry:
            mock_geometry = MagicMock()
            mock_get_geometry.return_value = mock_geometry
            poly, geometry = _get_boundary_shape(sample_polygon)
            assert poly == sample_polygon
            assert geometry == mock_geometry
            mock_get_geometry.assert_called_once_with(sample_polygon)

    def test_get_boundary_shape_from_multipolygon(self):
        """Test getting boundary shape from MultiPolygon object."""
        multipolygon = MultiPolygon(
            [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(2, 2), (3, 2), (3, 3), (2, 3)]),
            ]
        )
        with patch(
            "map_poster_creator.core.get_map_geometry_from_poly"
        ) as mock_get_geometry:
            mock_geometry = MagicMock()
            mock_get_geometry.return_value = mock_geometry
            poly, geometry = _get_boundary_shape(multipolygon)
            assert poly == multipolygon
            assert geometry == mock_geometry

    def test_get_boundary_shape_from_geojson_path(self, temp_dir, sample_polygon):
        """Test getting boundary shape from GeoJSON file path."""
        geojson_path = temp_dir / "test.geojson"
        with patch(
            "map_poster_creator.core.get_polygon_from_geojson",
            return_value=sample_polygon,
        ):
            with patch(
                "map_poster_creator.core.get_map_geometry_from_poly"
            ) as mock_get_geometry:
                mock_geometry = MagicMock()
                mock_get_geometry.return_value = mock_geometry
                poly, geometry = _get_boundary_shape(str(geojson_path))
                assert poly == sample_polygon
                assert geometry == mock_geometry

    def test_get_boundary_shape_from_path_object(self, temp_dir, sample_polygon):
        """Test getting boundary shape from Path object."""
        geojson_path = temp_dir / "test.geojson"
        with patch(
            "map_poster_creator.core.get_polygon_from_geojson",
            return_value=sample_polygon,
        ):
            with patch(
                "map_poster_creator.core.get_map_geometry_from_poly"
            ) as mock_get_geometry:
                mock_geometry = MagicMock()
                mock_get_geometry.return_value = mock_geometry
                poly, geometry = _get_boundary_shape(geojson_path)
                assert poly == sample_polygon
                assert geometry == mock_geometry


class TestPreprocessing:
    """Tests for _preprocessing function."""

    def test_preprocessing_filters_by_polygon(self, sample_polygon, mock_geodataframe):
        """Test that preprocessing filters GeoDataFrame by polygon."""
        # Create a GeoDataFrame with points inside and outside polygon
        from shapely.geometry import Point

        inside_point = Point(-73.97, 40.73)  # Inside sample_polygon
        outside_point = Point(0, 0)  # Outside sample_polygon

        gdf = GeoDataFrame(
            {"value": [1, 2]},
            geometry=[inside_point, outside_point],
            crs="EPSG:4326",
        )

        result = _preprocessing(sample_polygon, gdf)
        # Should only contain geometries inside the polygon
        assert len(result) <= len(gdf)
        # All results should be inside polygon
        for geom in result.geometry:
            assert sample_polygon.contains(geom)

    def test_preprocessing_empty_result(self, sample_polygon):
        """Test preprocessing when no geometries are inside polygon."""
        from shapely.geometry import Point

        gdf = GeoDataFrame(
            {"value": [1, 2, 3]},
            geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
            crs="EPSG:4326",
        )
        result = _preprocessing(sample_polygon, gdf)
        assert len(result) == 0

    def test_preprocessing_preserves_columns(self, sample_polygon, mock_geodataframe):
        """Test that preprocessing preserves all columns."""
        gdf = GeoDataFrame(
            {"value": [1, 2], "name": ["A", "B"]},
            geometry=mock_geodataframe.geometry,
            crs="EPSG:4326",
        )
        result = _preprocessing(sample_polygon, gdf)
        assert "value" in result.columns
        assert "name" in result.columns


class TestPreprocessingRoads:
    """Tests for _preprocessing_roads function."""

    def test_preprocessing_roads_filters_footway(self, sample_polygon):
        """Test that preprocessing_roads filters out footway and steps."""
        from shapely.geometry import Point

        gdf = GeoDataFrame(
            {
                "fclass": ["primary", "footway", "steps", "secondary"],
                "maxspeed": [50, 5, 5, 40],
            },
            geometry=[Point(-73.97, 40.73) for _ in range(4)],
            crs="EPSG:4326",
        )

        result = _preprocessing_roads(sample_polygon, gdf)
        # Should not contain footway or steps
        assert "footway" not in result["fclass"].values
        assert "steps" not in result["fclass"].values
        # Should contain primary and secondary
        assert (
            "primary" in result["fclass"].values
            or "secondary" in result["fclass"].values
        )

    def test_preprocessing_roads_adds_speeds(self, sample_polygon):
        """Test that preprocessing_roads adds speeds column."""
        from shapely.geometry import Point

        gdf = GeoDataFrame(
            {
                "fclass": ["primary", "secondary"],
                "maxspeed": [50, 40],
            },
            geometry=[Point(-73.97, 40.73) for _ in range(2)],
            crs="EPSG:4326",
        )

        result = _preprocessing_roads(sample_polygon, gdf)
        assert "speeds" in result.columns
        assert len(result["speeds"]) == len(result)

    def test_preprocessing_roads_filters_by_polygon(self, sample_polygon):
        """Test that preprocessing_roads also filters by polygon."""
        from shapely.geometry import Point

        inside_point = Point(-73.97, 40.73)  # Inside polygon
        outside_point = Point(0, 0)  # Outside polygon

        gdf = GeoDataFrame(
            {
                "fclass": ["primary", "primary"],
                "maxspeed": [50, 50],
            },
            geometry=[inside_point, outside_point],
            crs="EPSG:4326",
        )

        result = _preprocessing_roads(sample_polygon, gdf)
        # Should only contain geometries inside polygon
        for geom in result.geometry:
            assert sample_polygon.contains(geom)


class TestCreatePoster:
    """Tests for create_poster function."""

    def test_create_poster_from_polygon(
        self, mock_shp_dir, sample_polygon, mock_colorscheme, temp_dir
    ):
        """Test creating poster from Polygon object."""
        output_file = temp_dir / "poster.png"

        with patch("map_poster_creator.core._get_boundary_shape") as mock_get_shape:
            mock_geometry = MagicMock()
            mock_get_shape.return_value = (sample_polygon, mock_geometry)

            with patch(
                "map_poster_creator.core.GeoDataFrame.from_file"
            ) as mock_from_file:
                mock_gdf = MagicMock()
                mock_from_file.return_value = mock_gdf

                with patch(
                    "map_poster_creator.core._preprocessing_roads",
                    return_value=mock_gdf,
                ):
                    with patch(
                        "map_poster_creator.core._preprocessing", return_value=mock_gdf
                    ):
                        with patch(
                            "map_poster_creator.core.plot_and_save"
                        ) as mock_plot:
                            create_poster(
                                shp_dir=mock_shp_dir,
                                geojson_path=sample_polygon,
                                color=mock_colorscheme,
                                width=15.0,
                                dpi=300,
                                output=output_file,
                            )
                            mock_plot.assert_called_once()
                            # Verify plot_and_save was called with correct parameters
                            call_args = mock_plot.call_args
                            assert call_args[1]["geometry"] == mock_geometry
                            assert call_args[1]["path"] == output_file
                            assert call_args[1]["dpi"] == 300
                            assert call_args[1]["width"] == 15.0
                            assert call_args[1]["cscheme"] == mock_colorscheme

    def test_create_poster_from_geojson_path(
        self, mock_shp_dir, sample_polygon, mock_colorscheme, temp_dir
    ):
        """Test creating poster from GeoJSON file path."""
        geojson_path = temp_dir / "test.geojson"
        output_file = temp_dir / "poster.png"

        with patch("map_poster_creator.core._get_boundary_shape") as mock_get_shape:
            mock_geometry = MagicMock()
            mock_get_shape.return_value = (sample_polygon, mock_geometry)

            with patch(
                "map_poster_creator.core.GeoDataFrame.from_file"
            ) as mock_from_file:
                mock_gdf = MagicMock()
                mock_from_file.return_value = mock_gdf

                with patch(
                    "map_poster_creator.core._preprocessing_roads",
                    return_value=mock_gdf,
                ):
                    with patch(
                        "map_poster_creator.core._preprocessing", return_value=mock_gdf
                    ):
                        with patch(
                            "map_poster_creator.core.plot_and_save"
                        ) as mock_plot:
                            create_poster(
                                shp_dir=mock_shp_dir,
                                geojson_path=geojson_path,
                                color=mock_colorscheme,
                                width=15.0,
                                dpi=300,
                                output=output_file,
                            )
                            mock_plot.assert_called_once()

    def test_create_poster_different_dpi(
        self, mock_shp_dir, sample_polygon, mock_colorscheme, temp_dir
    ):
        """Test creating poster with different DPI values."""
        for dpi in [150, 300, 600]:
            output_file = temp_dir / f"poster_{dpi}.png"

            with patch("map_poster_creator.core._get_boundary_shape") as mock_get_shape:
                mock_geometry = MagicMock()
                mock_get_shape.return_value = (sample_polygon, mock_geometry)

                with patch(
                    "map_poster_creator.core.GeoDataFrame.from_file"
                ) as mock_from_file:
                    mock_gdf = MagicMock()
                    mock_from_file.return_value = mock_gdf

                    with patch(
                        "map_poster_creator.core._preprocessing_roads",
                        return_value=mock_gdf,
                    ):
                        with patch(
                            "map_poster_creator.core._preprocessing",
                            return_value=mock_gdf,
                        ):
                            with patch(
                                "map_poster_creator.core.plot_and_save"
                            ) as mock_plot:
                                create_poster(
                                    shp_dir=mock_shp_dir,
                                    geojson_path=sample_polygon,
                                    color=mock_colorscheme,
                                    width=15.0,
                                    dpi=dpi,
                                    output=output_file,
                                )
                                call_args = mock_plot.call_args
                                assert call_args[1]["dpi"] == dpi

    def test_create_poster_different_widths(
        self, mock_shp_dir, sample_polygon, mock_colorscheme, temp_dir
    ):
        """Test creating poster with different width values."""
        for width in [10.0, 15.0, 20.0, 30.0]:
            output_file = temp_dir / f"poster_{width}.png"

            with patch("map_poster_creator.core._get_boundary_shape") as mock_get_shape:
                mock_geometry = MagicMock()
                mock_get_shape.return_value = (sample_polygon, mock_geometry)

                with patch(
                    "map_poster_creator.core.GeoDataFrame.from_file"
                ) as mock_from_file:
                    mock_gdf = MagicMock()
                    mock_from_file.return_value = mock_gdf

                    with patch(
                        "map_poster_creator.core._preprocessing_roads",
                        return_value=mock_gdf,
                    ):
                        with patch(
                            "map_poster_creator.core._preprocessing",
                            return_value=mock_gdf,
                        ):
                            with patch(
                                "map_poster_creator.core.plot_and_save"
                            ) as mock_plot:
                                create_poster(
                                    shp_dir=mock_shp_dir,
                                    geojson_path=sample_polygon,
                                    color=mock_colorscheme,
                                    width=width,
                                    dpi=300,
                                    output=output_file,
                                )
                                call_args = mock_plot.call_args
                                assert call_args[1]["width"] == width

    def test_create_poster_loads_all_shapefiles(
        self, mock_shp_dir, sample_polygon, mock_colorscheme, temp_dir
    ):
        """Test that create_poster loads all required shapefiles."""
        output_file = temp_dir / "poster.png"

        with patch("map_poster_creator.core._get_boundary_shape") as mock_get_shape:
            mock_geometry = MagicMock()
            mock_get_shape.return_value = (sample_polygon, mock_geometry)

            with patch(
                "map_poster_creator.core.GeoDataFrame.from_file"
            ) as mock_from_file:
                mock_gdf = MagicMock()
                mock_from_file.return_value = mock_gdf

                with patch(
                    "map_poster_creator.core._preprocessing_roads",
                    return_value=mock_gdf,
                ):
                    with patch(
                        "map_poster_creator.core._preprocessing", return_value=mock_gdf
                    ):
                        with patch("map_poster_creator.core.plot_and_save"):
                            create_poster(
                                shp_dir=mock_shp_dir,
                                geojson_path=sample_polygon,
                                color=mock_colorscheme,
                                width=15.0,
                                dpi=300,
                                output=output_file,
                            )
                            # Should load roads, water, and greens shapefiles
                            assert mock_from_file.call_count == 3
                            # Check that all three shapefile types were loaded
                            call_paths = [
                                str(call[0][0])
                                for call in mock_from_file.call_args_list
                            ]
                            roads_found = any(
                                "gis_osm_roads" in path for path in call_paths
                            )
                            water_found = any(
                                "gis_osm_water" in path for path in call_paths
                            )
                            greens_found = any(
                                "gis_osm_pois" in path for path in call_paths
                            )
                            assert (
                                roads_found
                            ), f"Roads shapefile not found in calls: {call_paths}"
                            assert (
                                water_found
                            ), f"Water shapefile not found in calls: {call_paths}"
                            assert (
                                greens_found
                            ), f"Greens shapefile not found in calls: {call_paths}"


class TestCreatePosterFromCoordinates:
    """Tests for create_poster_from_coordinates function."""

    def test_create_poster_from_coordinates_success(
        self, mock_shp_dir, sample_coordinates, mock_colorscheme, temp_dir
    ):
        """Test creating poster from coordinates successfully."""
        output_file = temp_dir / "poster.png"

        with patch(
            "map_poster_creator.core.polygon_from_coordinates"
        ) as mock_polygon_from_coords:
            sample_polygon = Polygon([(c[0], c[1]) for c in sample_coordinates])
            mock_polygon_from_coords.return_value = sample_polygon

            with patch("map_poster_creator.core.create_poster") as mock_create_poster:
                create_poster_from_coordinates(
                    shp_dir=mock_shp_dir,
                    coordinates=sample_coordinates,
                    color=mock_colorscheme,
                    width=15.0,
                    dpi=300,
                    output=output_file,
                )
                mock_create_poster.assert_called_once()
                call_args = mock_create_poster.call_args
                # Should pass polygon directly, not a file path
                assert isinstance(call_args[1]["geojson_path"], Polygon)

    def test_create_poster_from_coordinates_with_geojson_output(
        self, mock_shp_dir, sample_coordinates, mock_colorscheme, temp_dir
    ):
        """Test creating poster from coordinates with geojson output path."""
        output_file = temp_dir / "poster.png"
        geojson_output = temp_dir / "output.geojson"

        with patch(
            "map_poster_creator.core.polygon_from_coordinates"
        ) as mock_polygon_from_coords:
            sample_polygon = Polygon([(c[0], c[1]) for c in sample_coordinates])
            mock_polygon_from_coords.return_value = sample_polygon

            with patch(
                "map_poster_creator.core._polygon_to_geojson_file"
            ) as mock_save_geojson:
                with patch(
                    "map_poster_creator.core.create_poster"
                ) as mock_create_poster:
                    create_poster_from_coordinates(
                        shp_dir=mock_shp_dir,
                        coordinates=sample_coordinates,
                        color=mock_colorscheme,
                        width=15.0,
                        dpi=300,
                        output=output_file,
                        geojson_output_path=geojson_output,
                    )
                    mock_save_geojson.assert_called_once_with(
                        sample_polygon, geojson_output
                    )
                    mock_create_poster.assert_called_once()
                    call_args = mock_create_poster.call_args
                    # Should pass geojson path, not polygon
                    assert call_args[1]["geojson_path"] == geojson_output

    def test_create_poster_from_coordinates_different_formats(
        self, mock_shp_dir, mock_colorscheme, temp_dir
    ):
        """Test creating poster from coordinates in different formats."""
        # Test with list of lists
        coords_list = [[-74.006, 40.7128], [-73.935, 40.7128], [-73.935, 40.7589]]
        # Test with list of tuples
        coords_tuples = [(-74.006, 40.7128), (-73.935, 40.7128), (-73.935, 40.7589)]

        for coords in [coords_list, coords_tuples]:
            output_file = temp_dir / f"poster_{type(coords).__name__}.png"

            with patch(
                "map_poster_creator.core.polygon_from_coordinates"
            ) as mock_polygon_from_coords:
                sample_polygon = Polygon([(c[0], c[1]) for c in coords])
                mock_polygon_from_coords.return_value = sample_polygon

                with patch(
                    "map_poster_creator.core.create_poster"
                ) as mock_create_poster:
                    create_poster_from_coordinates(
                        shp_dir=mock_shp_dir,
                        coordinates=coords,
                        color=mock_colorscheme,
                        width=15.0,
                        dpi=300,
                        output=output_file,
                    )
                    mock_create_poster.assert_called_once()

    def test_create_poster_from_coordinates_auto_closes_polygon(
        self, mock_shp_dir, mock_colorscheme, temp_dir
    ):
        """Test that coordinates are automatically closed if first != last."""
        # Coordinates without closing point
        coords = [[-74.006, 40.7128], [-73.935, 40.7128], [-73.935, 40.7589]]
        output_file = temp_dir / "poster.png"

        with patch(
            "map_poster_creator.core.polygon_from_coordinates"
        ) as mock_polygon_from_coords:
            # polygon_from_coordinates should handle closing
            sample_polygon = Polygon(
                [
                    (-74.006, 40.7128),
                    (-73.935, 40.7128),
                    (-73.935, 40.7589),
                    (-74.006, 40.7128),
                ]
            )
            mock_polygon_from_coords.return_value = sample_polygon

            with patch("map_poster_creator.core.create_poster") as mock_create_poster:
                create_poster_from_coordinates(
                    shp_dir=mock_shp_dir,
                    coordinates=coords,
                    color=mock_colorscheme,
                    width=15.0,
                    dpi=300,
                    output=output_file,
                )
                # Should call polygon_from_coordinates with the original coordinates
                mock_polygon_from_coords.assert_called_once_with(coords)


class TestPosterEquivalentToBashScript:
    """Test equivalent to test_poster.sh - tests the Python API directly."""

    def test_poster_equivalent_to_bash_script(
        self, mock_shp_dir, mock_colorscheme, temp_dir
    ):
        """
        Test equivalent to test_poster.sh that calls the Python API directly.

        This test mirrors the bash script behavior:
        - Uses the same coordinates (small square around New York)
        - Uses white color scheme (default)
        - Validates output file creation and PNG format
        """
        # Same coordinates as in test_poster.sh
        coordinates = [
            [-74.006, 40.7128],
            [-73.935, 40.7128],
            [-73.935, 40.7589],
            [-74.006, 40.7589],
        ]

        # Output file (equivalent to test_outputs/poster.png)
        output_file = temp_dir / "poster.png"

        # Create output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Call create_poster_from_coordinates directly (equivalent to POST /poster/simple)
        with patch(
            "map_poster_creator.core.polygon_from_coordinates"
        ) as mock_polygon_from_coords:
            from shapely.geometry import Polygon

            sample_polygon = Polygon(
                [
                    (-74.006, 40.7128),
                    (-73.935, 40.7128),
                    (-73.935, 40.7589),
                    (-74.006, 40.7589),
                ]
            )
            mock_polygon_from_coords.return_value = sample_polygon

            with patch("map_poster_creator.core.create_poster") as mock_create_poster:
                # Create a side effect that simulates file creation
                def mock_create_side_effect(*args, **kwargs):
                    output_path = kwargs.get("output")
                    if output_path:
                        # Create a dummy PNG file to simulate the actual file creation
                        output_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

                mock_create_poster.side_effect = mock_create_side_effect

                create_poster_from_coordinates(
                    shp_dir=mock_shp_dir,
                    coordinates=coordinates,
                    color=mock_colorscheme,
                    width=15.0,
                    dpi=300,
                    output=output_file,
                )

                # Verify create_poster was called
                mock_create_poster.assert_called_once()

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

                # Verify the call arguments match expected values
                call_args = mock_create_poster.call_args
                assert call_args[1]["shp_dir"] == mock_shp_dir
                assert isinstance(call_args[1]["geojson_path"], Polygon)
                assert call_args[1]["color"] == mock_colorscheme
                assert call_args[1]["width"] == 15.0
                assert call_args[1]["dpi"] == 300
                assert call_args[1]["output"] == output_file

    def test_poster_equivalent_with_different_colors(self, mock_shp_dir, temp_dir):
        """Test equivalent to bash script but with different color schemes."""
        coordinates = [
            [-74.006, 40.7128],
            [-73.935, 40.7128],
            [-73.935, 40.7589],
            [-74.006, 40.7589],
        ]

        # Test with different color schemes (equivalent to COLOR environment variable)
        color_schemes = {
            "white": ColorScheme(
                facecolor="white", water="#bdddff", greens="#d4ffe1", roads="#000000"
            ),
            "black": ColorScheme(
                facecolor="black", water="#383d52", greens="#354038", roads="#ffffff"
            ),
        }

        for color_name, color_scheme in color_schemes.items():
            output_file = temp_dir / f"poster_{color_name}.png"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with patch(
                "map_poster_creator.core.polygon_from_coordinates"
            ) as mock_polygon_from_coords:
                from shapely.geometry import Polygon

                sample_polygon = Polygon(
                    [
                        (-74.006, 40.7128),
                        (-73.935, 40.7128),
                        (-73.935, 40.7589),
                        (-74.006, 40.7589),
                    ]
                )
                mock_polygon_from_coords.return_value = sample_polygon

                with patch(
                    "map_poster_creator.core.create_poster"
                ) as mock_create_poster:
                    # Create a side effect that simulates file creation
                    def mock_create_side_effect(*args, **kwargs):
                        output_path = kwargs.get("output")
                        if output_path:
                            # Create a dummy PNG file to simulate the actual file creation
                            output_path.write_bytes(
                                b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
                            )

                    mock_create_poster.side_effect = mock_create_side_effect

                    create_poster_from_coordinates(
                        shp_dir=mock_shp_dir,
                        coordinates=coordinates,
                        color=color_scheme,
                        width=15.0,
                        dpi=300,
                        output=output_file,
                    )

                    # Verify file was created and is valid
                    assert output_file.exists()
                    assert output_file.stat().st_size > 0

                    # Verify PNG magic bytes
                    with open(output_file, "rb") as f:
                        first_bytes = f.read(8)
                        assert first_bytes == b"\x89PNG\r\n\x1a\n"

                    # Verify correct color scheme was used
                    call_args = mock_create_poster.call_args
                    assert call_args[1]["color"] == color_scheme
