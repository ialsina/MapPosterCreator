"""Comprehensive tests for data/core.py functions."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pandas import DataFrame, Series
from shapely.geometry import Point, Polygon

from map_poster_creator.data.core import (
    _calculate_point_choose,
    _extract_shp_url,
    find_download_shp,
    find_download_shp_from_point,
    get_geojson_path_from_geoboundaries,
    resolve_city,
)


class TestResolveCity:
    """Tests for resolve_city function."""

    def test_resolve_city_without_country(self, mock_city_df):
        """Test resolving city without country."""
        with patch("map_poster_creator.data.core.get_city_df", return_value=mock_city_df):
            result = resolve_city("New York", interactive=False, first=True)
            assert isinstance(result, Series)
            assert result["name"] == "New York"

    def test_resolve_city_with_country(self, mock_city_df, mock_country_df):
        """Test resolving city with country."""
        with patch("map_poster_creator.data.core.get_city_df", return_value=mock_city_df):
            with patch(
                "map_poster_creator.data.core.get_country_df",
                return_value=mock_country_df,
            ):
                result = resolve_city(
                    "New York", country="United States", interactive=False, first=True
                )
                assert isinstance(result, Series)

    def test_resolve_city_not_found(self):
        """Test resolving city that doesn't exist."""
        # Create empty DataFrame with required columns
        empty_df = DataFrame(
            columns=[
                "name",
                "asciiname",
                "country code",
                "population",
                "alternatenames",
            ]
        )
        with patch("map_poster_creator.data.core.get_city_df", return_value=empty_df):
            result = resolve_city("Nonexistent City", interactive=False)
            assert result is None

    def test_resolve_city_interactive_single_match(self, mock_city_df):
        """Test resolving city in interactive mode with single match."""
        with patch("map_poster_creator.data.core.get_city_df", return_value=mock_city_df):
            result = resolve_city("New York", interactive=True, element_if_one=True)
            assert isinstance(result, Series)

    def test_resolve_city_interactive_multiple_matches(self, mock_city_df):
        """Test resolving city in interactive mode with multiple matches."""
        # Create DataFrame with multiple cities
        multiple_cities = DataFrame(
            [
                {
                    "name": "New York",
                    "asciiname": "New York",
                    "country code": "US",
                    "population": 8175133,
                    "alternatenames": "",
                },
                {
                    "name": "New York",
                    "asciiname": "New York",
                    "country code": "CA",
                    "population": 1000,
                    "alternatenames": "",
                },
            ]
        )
        with patch("map_poster_creator.data.core.get_city_df", return_value=multiple_cities):
            # Without callback, should return first (highest population)
            result = resolve_city("New York", interactive=True, first=False)
            # When interactive=True and multiple matches without callback, returns first
            assert isinstance(result, Series)
            assert result["country code"] == "US"  # Highest population

    def test_resolve_city_interactive_callback(self, mock_city_df):
        """Test resolving city with interactive callback."""
        # Create DataFrame with multiple cities to trigger callback
        multiple_cities = DataFrame(
            [
                {
                    "name": "New York",
                    "asciiname": "New York",
                    "country code": "US",
                    "population": 8175133,
                    "alternatenames": "",
                },
                {
                    "name": "New York",
                    "asciiname": "New York",
                    "country code": "CA",
                    "population": 1000,
                    "alternatenames": "",
                },
            ]
        )
        callback = Mock(return_value=multiple_cities.iloc[0])
        with patch("map_poster_creator.data.core.get_city_df", return_value=multiple_cities):
            result = resolve_city("New York", interactive=True, interactive_callback=callback)
            # Callback is only called when there are multiple matches
            callback.assert_called_once()
            assert isinstance(result, Series)

    def test_resolve_city_first_flag(self, mock_city_df):
        """Test resolve_city with first=True flag."""
        with patch("map_poster_creator.data.core.get_city_df", return_value=mock_city_df):
            result = resolve_city("New York", interactive=False, first=True)
            assert isinstance(result, Series)

    def test_resolve_city_element_if_one(self, mock_city_df):
        """Test resolve_city with element_if_one flag."""
        with patch("map_poster_creator.data.core.get_city_df", return_value=mock_city_df):
            result = resolve_city("New York", interactive=False, element_if_one=True)
            assert isinstance(result, Series)

    def test_resolve_city_sorted_by_population(self, mock_city_df):
        """Test that cities are sorted by population."""
        # Use cities that share a common name so the search will match all of them
        # The search function does exact matches, so we need cities with the same base name
        # or use alternatenames to match
        multiple_cities = DataFrame(
            [
                {
                    "name": "Springfield",
                    "asciiname": "Springfield",
                    "country code": "US",
                    "population": 1000,
                    "alternatenames": "City A",
                },
                {
                    "name": "Springfield",
                    "asciiname": "Springfield",
                    "country code": "US",
                    "population": 5000,
                    "alternatenames": "City B",
                },
                {
                    "name": "Springfield",
                    "asciiname": "Springfield",
                    "country code": "US",
                    "population": 2000,
                    "alternatenames": "City C",
                },
            ]
        )
        with patch("map_poster_creator.data.core.get_city_df", return_value=multiple_cities):
            result = resolve_city("Springfield", interactive=False, first=True)
            # Should return highest population
            assert result["name"] == "Springfield"
            assert result["population"] == 5000
            # Verify it's the one with alternatenames "City B"
            assert result["alternatenames"] == "City B"


class TestGetGeojsonPathFromGeoboundaries:
    """Tests for get_geojson_path_from_geoboundaries function."""

    def test_get_geojson_path_with_city(self, mock_city_series, temp_dir, sample_polygon):
        """Test getting GeoJSON path with city name."""
        with patch("map_poster_creator.data.core.paths") as mock_paths:
            mock_paths.geojson_path = temp_dir / "geojson"
            mock_paths.geojson_path.mkdir(parents=True, exist_ok=True)

            with patch(
                "map_poster_creator.data.core.resolve_city",
                return_value=mock_city_series,
            ):
                with patch(
                    "map_poster_creator.data.core._get_city_polygon_from_geoboundaries",
                    return_value=sample_polygon,
                ):
                    with patch(
                        "map_poster_creator.data.core._polygon_to_geojson_file"
                    ) as mock_save:
                        result = get_geojson_path_from_geoboundaries("New York", interactive=False)
                        assert isinstance(result, Path)
                        mock_save.assert_called_once()

    def test_get_geojson_path_with_country_code(self, mock_city_df, temp_dir, sample_polygon):
        """Test getting GeoJSON path with country code."""
        with patch("map_poster_creator.data.core.paths") as mock_paths:
            mock_paths.geojson_path = temp_dir / "geojson"
            mock_paths.geojson_path.mkdir(parents=True, exist_ok=True)

            with patch("map_poster_creator.data.core.get_city_df", return_value=mock_city_df):
                with patch(
                    "map_poster_creator.data.core._get_city_polygon_from_geoboundaries",
                    return_value=sample_polygon,
                ):
                    with patch(
                        "map_poster_creator.data.core._polygon_to_geojson_file"
                    ) as mock_save:
                        result = get_geojson_path_from_geoboundaries(
                            "New York", country_code="US", interactive=False
                        )
                        assert isinstance(result, Path)
                        mock_save.assert_called_once()

    def test_get_geojson_path_file_exists(self, mock_city_series, temp_dir):
        """Test getting GeoJSON path when file already exists."""
        with patch("map_poster_creator.data.core.paths") as mock_paths:
            mock_paths.geojson_path = temp_dir / "geojson"
            mock_paths.geojson_path.mkdir(parents=True, exist_ok=True)
            existing_file = mock_paths.geojson_path / "New York_US.geojson"
            existing_file.touch()

            with patch(
                "map_poster_creator.data.core.resolve_city",
                return_value=mock_city_series,
            ):
                result = get_geojson_path_from_geoboundaries("New York", interactive=False)
                assert result == existing_file

    def test_get_geojson_path_city_not_found(self):
        """Test getting GeoJSON path when city is not found."""
        with patch("map_poster_creator.data.core.resolve_city", return_value=None):
            with pytest.raises(ValueError) as exc_info:
                get_geojson_path_from_geoboundaries("Nonexistent City", interactive=False)
            assert "did not give any results" in str(exc_info.value)

    def test_get_geojson_path_geoboundary_not_found(self, mock_city_series):
        """Test getting GeoJSON path when geoboundary is not found."""
        with patch("map_poster_creator.data.core.paths") as mock_paths:
            mock_paths.geojson_path = Path("/tmp/geojson")

            with patch(
                "map_poster_creator.data.core.resolve_city",
                return_value=mock_city_series,
            ):
                with patch(
                    "map_poster_creator.data.core._get_city_polygon_from_geoboundaries",
                    side_effect=ValueError("Geoboundary not found"),
                ):
                    with pytest.raises(ValueError) as exc_info:
                        get_geojson_path_from_geoboundaries("New York", interactive=False)
                    assert "Could not find geoboundary" in str(exc_info.value)

    def test_get_geojson_path_interactive_mode(self, mock_city_series, temp_dir, sample_polygon):
        """Test getting GeoJSON path in interactive mode."""
        with patch("map_poster_creator.data.core.paths") as mock_paths:
            mock_paths.geojson_path = temp_dir / "geojson"
            mock_paths.geojson_path.mkdir(parents=True, exist_ok=True)

            with patch(
                "map_poster_creator.data.core.resolve_city",
                return_value=mock_city_series,
            ):
                with patch(
                    "map_poster_creator.data.core._get_city_polygon_from_geoboundaries",
                    return_value=sample_polygon,
                ):
                    with patch("map_poster_creator.data.core._ask_reuse", return_value=False):
                        with patch(
                            "map_poster_creator.data.core._polygon_to_geojson_file"
                        ) as mock_save:
                            result = get_geojson_path_from_geoboundaries(
                                "New York", interactive=True
                            )
                            assert isinstance(result, Path)
                            mock_save.assert_called_once()


class TestExtractShpUrl:
    """Tests for _extract_shp_url function."""

    def test_extract_shp_url_success(self, mock_region_node, mock_geofabrik_urls):
        """Test extracting SHP URL successfully."""
        with patch(
            "map_poster_creator.data.core.get_geofabrik_urls",
            return_value=mock_geofabrik_urls,
        ):
            with patch("map_poster_creator.data.core.is_valid_download_url", return_value=True):
                result = _extract_shp_url(mock_region_node)
                assert isinstance(result, str)
                assert result.endswith(".shp.zip")

    def test_extract_shp_url_no_valid_url(self, mock_region_node):
        """Test extracting SHP URL when no valid URL is found."""
        invalid_urls = {"north-america/us": ["https://example.com/invalid.zip"]}
        with patch("map_poster_creator.data.core.get_geofabrik_urls", return_value=invalid_urls):
            with patch("map_poster_creator.data.core.is_valid_download_url", return_value=False):
                with pytest.raises(ValueError) as exc_info:
                    _extract_shp_url(mock_region_node)
                assert "Couldn't find a satisfying" in str(exc_info.value)


class TestCalculatePointChoose:
    """Tests for _calculate_point_choose function."""

    def test_calculate_point_choose_success(self, sample_point, mock_region_node, sample_polygon):
        """Test calculating point choose successfully."""
        sorted_distances = [(mock_region_node, 0.1)]
        with patch(
            "map_poster_creator.data.core.get_region_polygons",
            return_value=[sample_polygon],
        ):
            with patch("map_poster_creator.data.core.is_point_in_polygon", return_value=True):
                result = _calculate_point_choose(sample_point, sorted_distances)
                assert result == mock_region_node

    def test_calculate_point_choose_no_match(self, sample_point, mock_region_node):
        """Test calculating point choose when no polygon matches."""
        sorted_distances = [(mock_region_node, 0.1)]
        empty_polygon = Polygon([(100, 100), (101, 100), (101, 101), (100, 101)])
        with patch(
            "map_poster_creator.data.core.get_region_polygons",
            return_value=[empty_polygon],
        ):
            with patch("map_poster_creator.data.core.is_point_in_polygon", return_value=False):
                with pytest.raises(ValueError) as exc_info:
                    _calculate_point_choose(sample_point, sorted_distances)
                assert "Couldn't find a satisfying region" in str(exc_info.value)


class TestFindDownloadShpFromPoint:
    """Tests for find_download_shp_from_point function."""

    def test_find_download_shp_from_point_success(
        self, sample_point, mock_shp_dir, mock_region_node
    ):
        """Test finding and downloading SHP from point successfully."""
        with patch(
            "map_poster_creator.data.core.get_region_centroids",
            return_value={mock_region_node: [sample_point]},
        ):
            with patch(
                "map_poster_creator.data.core._extract_shp_url",
                return_value="https://example.com/shp.zip",
            ):
                with patch(
                    "map_poster_creator.data.core._download_extract_shp",
                    return_value=mock_shp_dir,
                ):
                    result = find_download_shp_from_point(
                        sample_point, calculate_point=False, interactive=False
                    )
                    assert result == mock_shp_dir

    def test_find_download_shp_from_point_calculate_point(
        self, sample_point, mock_shp_dir, mock_region_node, sample_polygon
    ):
        """Test finding SHP with calculate_point=True."""
        with patch(
            "map_poster_creator.data.core.get_region_centroids",
            return_value={mock_region_node: [sample_point]},
        ):
            with patch(
                "map_poster_creator.data.core._calculate_point_choose",
                return_value=mock_region_node,
            ):
                with patch(
                    "map_poster_creator.data.core._extract_shp_url",
                    return_value="https://example.com/shp.zip",
                ):
                    with patch(
                        "map_poster_creator.data.core._download_extract_shp",
                        return_value=mock_shp_dir,
                    ):
                        result = find_download_shp_from_point(
                            sample_point, calculate_point=True, interactive=False
                        )
                        assert result == mock_shp_dir

    def test_find_download_shp_from_point_interactive(
        self, sample_point, mock_shp_dir, mock_region_node
    ):
        """Test finding SHP in interactive mode."""
        callback = Mock(return_value=mock_region_node)
        with patch("map_poster_creator.data.core.get_region_centroids") as mock_get_centroids:
            # Return a dict with region_node as key and list of centroids as value
            # The function calculates distances, so we need to provide centroids that will work
            mock_get_centroids.return_value = {mock_region_node: [sample_point]}
            with patch(
                "map_poster_creator.data.core._extract_shp_url",
                return_value="https://example.com/shp.zip",
            ):
                with patch(
                    "map_poster_creator.data.core._download_extract_shp",
                    return_value=mock_shp_dir,
                ):
                    result = find_download_shp_from_point(
                        sample_point,
                        calculate_point=False,
                        interactive=True,
                        interactive_callback=callback,
                    )
                    assert result == mock_shp_dir
                    # Verify callback was called with sorted_distances list
                    callback.assert_called_once()
                    # Check that it was called with a list of (region_node, distance) tuples
                    call_args = callback.call_args[0]
                    assert len(call_args) == 1
                    assert isinstance(call_args[0], list)
                    assert len(call_args[0]) > 0
                    # Each element should be a tuple of (region_node, distance)
                    assert isinstance(call_args[0][0], tuple)
                    assert len(call_args[0][0]) == 2
                    # The first element of the tuple should be the region node
                    assert call_args[0][0][0] == mock_region_node

    def test_find_download_shp_from_point_no_callback(
        self, sample_point, mock_shp_dir, mock_region_node
    ):
        """Test finding SHP in interactive mode without callback."""
        with patch(
            "map_poster_creator.data.core.get_region_centroids",
            return_value={mock_region_node: [sample_point]},
        ):
            with patch(
                "map_poster_creator.data.core._extract_shp_url",
                return_value="https://example.com/shp.zip",
            ):
                with patch(
                    "map_poster_creator.data.core._download_extract_shp",
                    return_value=mock_shp_dir,
                ):
                    result = find_download_shp_from_point(
                        sample_point,
                        calculate_point=False,
                        interactive=True,
                        interactive_callback=None,
                    )
                    assert result == mock_shp_dir

    def test_find_download_shp_from_point_custom_location_name(
        self, sample_point, mock_shp_dir, mock_region_node
    ):
        """Test finding SHP with custom location name."""
        with patch(
            "map_poster_creator.data.core.get_region_centroids",
            return_value={mock_region_node: [sample_point]},
        ):
            with patch(
                "map_poster_creator.data.core._extract_shp_url",
                return_value="https://example.com/shp.zip",
            ):
                with patch(
                    "map_poster_creator.data.core._download_extract_shp",
                    return_value=mock_shp_dir,
                ):
                    result = find_download_shp_from_point(
                        sample_point,
                        calculate_point=False,
                        interactive=False,
                        location_name="custom location",
                    )
                    assert result == mock_shp_dir


class TestFindDownloadShp:
    """Tests for find_download_shp function."""

    def test_find_download_shp_success(self, mock_city_series, sample_point, mock_shp_dir):
        """Test finding and downloading SHP for a city successfully."""
        with patch("map_poster_creator.data.core.resolve_city", return_value=mock_city_series):
            with patch(
                "map_poster_creator.data.core.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ):
                result = find_download_shp("New York", country="United States", interactive=False)
                assert result == mock_shp_dir

    def test_find_download_shp_city_not_found(self):
        """Test finding SHP when city is not found."""
        with patch("map_poster_creator.data.core.resolve_city", return_value=None):
            with pytest.raises(ValueError) as exc_info:
                find_download_shp("Nonexistent City", interactive=False)
            assert "did not give any results" in str(exc_info.value)

    def test_find_download_shp_with_country(self, mock_city_series, sample_point, mock_shp_dir):
        """Test finding SHP with country parameter."""
        with patch("map_poster_creator.data.core.resolve_city", return_value=mock_city_series):
            with patch(
                "map_poster_creator.data.core.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ) as mock_find:
                result = find_download_shp("New York", country="United States", interactive=False)
                assert result == mock_shp_dir
                # Verify that find_download_shp_from_point was called with correct point
                mock_find.assert_called_once()
                call_args = mock_find.call_args
                assert isinstance(call_args[1]["point"], Point)

    def test_find_download_shp_calculate_point(self, mock_city_series, sample_point, mock_shp_dir):
        """Test finding SHP with calculate_point=True."""
        with patch("map_poster_creator.data.core.resolve_city", return_value=mock_city_series):
            with patch(
                "map_poster_creator.data.core.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ) as mock_find:
                result = find_download_shp("New York", calculate_point=True, interactive=False)
                assert result == mock_shp_dir
                call_args = mock_find.call_args
                assert call_args[1]["calculate_point"] is True

    def test_find_download_shp_interactive(self, mock_city_series, sample_point, mock_shp_dir):
        """Test finding SHP in interactive mode."""
        city_callback = Mock(return_value=mock_city_series)
        region_callback = Mock(return_value=Mock())
        with patch("map_poster_creator.data.core.resolve_city", return_value=mock_city_series):
            with patch(
                "map_poster_creator.data.core.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ) as mock_find:
                result = find_download_shp(
                    "New York",
                    interactive=True,
                    interactive_callback=city_callback,
                    region_callback=region_callback,
                )
                assert result == mock_shp_dir
                call_args = mock_find.call_args
                assert call_args[1]["interactive"] is True
                assert call_args[1]["interactive_callback"] == region_callback

    def test_find_download_shp_location_name(self, mock_city_series, sample_point, mock_shp_dir):
        """Test that location name includes city name."""
        with patch("map_poster_creator.data.core.resolve_city", return_value=mock_city_series):
            with patch(
                "map_poster_creator.data.core.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ) as mock_find:
                result = find_download_shp("New York", interactive=False)
                assert result == mock_shp_dir
                call_args = mock_find.call_args
                assert 'city "New York"' in call_args[1]["location_name"]
