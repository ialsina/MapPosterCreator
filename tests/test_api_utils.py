"""Tests for API utility functions."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from shapely.geometry import Point, Polygon

from map_poster_creator.api.utils import find_shp_from_polygon


class TestFindShpFromPolygon:
    """Tests for find_shp_from_polygon function."""

    def test_find_shp_with_city_success(
        self, sample_polygon, mock_shp_dir, mock_city_series
    ):
        """Test finding SHP with city name successfully."""
        with patch(
            "map_poster_creator.api.utils.resolve_city", return_value=mock_city_series
        ):
            with patch(
                "map_poster_creator.api.utils.find_download_shp",
                return_value=mock_shp_dir,
            ):
                result = find_shp_from_polygon(
                    sample_polygon, city="New York", country="United States"
                )
                assert result == mock_shp_dir

    def test_find_shp_with_city_resolve_fails(self, sample_polygon, mock_shp_dir):
        """Test finding SHP when city resolution fails, falls back to centroid."""
        with patch(
            "map_poster_creator.api.utils.resolve_city",
            side_effect=ValueError("City not found"),
        ):
            with patch(
                "map_poster_creator.api.utils.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ):
                result = find_shp_from_polygon(sample_polygon, city="Nonexistent City")
                assert result == mock_shp_dir

    def test_find_shp_with_city_not_implemented(self, sample_polygon, mock_shp_dir):
        """Test finding SHP when city resolution raises NotImplementedError."""
        with patch(
            "map_poster_creator.api.utils.resolve_city",
            side_effect=NotImplementedError("Not implemented"),
        ):
            with patch(
                "map_poster_creator.api.utils.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ):
                result = find_shp_from_polygon(sample_polygon, city="New York")
                assert result == mock_shp_dir

    def test_find_shp_without_city_uses_centroid(self, sample_polygon, mock_shp_dir):
        """Test finding SHP without city uses polygon centroid."""
        with patch(
            "map_poster_creator.api.utils.find_download_shp_from_point",
            return_value=mock_shp_dir,
        ) as mock_find:
            result = find_shp_from_polygon(sample_polygon)
            assert result == mock_shp_dir
            # Verify that find_download_shp_from_point was called with the centroid
            mock_find.assert_called_once()
            call_args = mock_find.call_args
            assert isinstance(call_args[1]["point"], Point)
            assert call_args[1]["calculate_point"] is True
            assert call_args[1]["interactive"] is False
            assert call_args[1]["location_name"] == "polygon centroid"

    def test_find_shp_all_methods_fail(self, sample_polygon):
        """Test finding SHP when all methods fail."""
        with patch(
            "map_poster_creator.api.utils.resolve_city",
            side_effect=ValueError("City not found"),
        ):
            with patch(
                "map_poster_creator.api.utils.find_download_shp_from_point",
                side_effect=ValueError("Point not found"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    find_shp_from_polygon(sample_polygon, city="Nonexistent City")
                assert exc_info.value.status_code == 400
                assert (
                    "Could not automatically determine SHP region"
                    in exc_info.value.detail
                )

    def test_find_shp_centroid_fails_with_not_implemented(self, sample_polygon):
        """Test finding SHP when centroid method raises NotImplementedError."""
        with patch(
            "map_poster_creator.api.utils.resolve_city",
            side_effect=ValueError("City not found"),
        ):
            with patch(
                "map_poster_creator.api.utils.find_download_shp_from_point",
                side_effect=NotImplementedError("Not implemented"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    find_shp_from_polygon(sample_polygon)
                assert exc_info.value.status_code == 400

    def test_find_shp_with_country_only(
        self, sample_polygon, mock_shp_dir, mock_city_series
    ):
        """Test finding SHP with country but no city."""
        with patch("map_poster_creator.api.utils.resolve_city", return_value=None):
            with patch(
                "map_poster_creator.api.utils.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ):
                result = find_shp_from_polygon(sample_polygon, country="United States")
                assert result == mock_shp_dir

    def test_find_shp_city_returns_none(self, sample_polygon, mock_shp_dir):
        """Test finding SHP when city resolution returns None."""
        with patch("map_poster_creator.api.utils.resolve_city", return_value=None):
            with patch(
                "map_poster_creator.api.utils.find_download_shp_from_point",
                return_value=mock_shp_dir,
            ):
                result = find_shp_from_polygon(sample_polygon, city="New York")
                assert result == mock_shp_dir

    def test_find_shp_different_polygon_shapes(self, mock_shp_dir):
        """Test finding SHP with different polygon shapes."""
        # Test with a triangle
        triangle = Polygon([(0, 0), (1, 0), (0.5, 1), (0, 0)])
        with patch(
            "map_poster_creator.api.utils.find_download_shp_from_point",
            return_value=mock_shp_dir,
        ):
            result = find_shp_from_polygon(triangle)
            assert result == mock_shp_dir

        # Test with a complex polygon
        complex_poly = Polygon(
            [
                (-74.0, 40.7),
                (-73.9, 40.7),
                (-73.9, 40.8),
                (-74.0, 40.8),
                (-74.05, 40.75),
                (-74.0, 40.7),
            ]
        )
        with patch(
            "map_poster_creator.api.utils.find_download_shp_from_point",
            return_value=mock_shp_dir,
        ):
            result = find_shp_from_polygon(complex_poly)
            assert result == mock_shp_dir

    def test_find_shp_city_callback_interaction(
        self, sample_polygon, mock_shp_dir, mock_city_series
    ):
        """Test that city resolution uses correct parameters."""
        with patch(
            "map_poster_creator.api.utils.resolve_city", return_value=mock_city_series
        ) as mock_resolve:
            with patch(
                "map_poster_creator.api.utils.find_download_shp",
                return_value=mock_shp_dir,
            ):
                find_shp_from_polygon(
                    sample_polygon, city="New York", country="United States"
                )
                mock_resolve.assert_called_once_with(
                    city="New York",
                    country="United States",
                    interactive=False,
                    first=True,
                )

    def test_find_shp_find_download_shp_parameters(
        self, sample_polygon, mock_shp_dir, mock_city_series
    ):
        """Test that find_download_shp is called with correct parameters."""
        with patch(
            "map_poster_creator.api.utils.resolve_city", return_value=mock_city_series
        ):
            with patch(
                "map_poster_creator.api.utils.find_download_shp",
                return_value=mock_shp_dir,
            ) as mock_find:
                find_shp_from_polygon(
                    sample_polygon, city="New York", country="United States"
                )
                mock_find.assert_called_once_with(
                    city="New York",
                    country="United States",
                    interactive=False,
                    calculate_point=True,
                )
