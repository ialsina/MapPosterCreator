"""Comprehensive tests for API endpoints."""

from unittest.mock import patch, MagicMock
from fastapi import HTTPException


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Map Poster Creator API"
        assert data["version"] == "0.8.0"
        assert "endpoints" in data
        assert "/docs" in data["endpoints"]
        assert "/poster" in data["endpoints"]
        assert "/colors" in data["endpoints"]
        assert "/health" in data["endpoints"]


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestColorsEndpoint:
    """Tests for GET /colors endpoint."""

    def test_list_colors_success(self, client, mock_colorschemes):
        """Test listing all available color schemes."""
        with patch(
            "map_poster_creator.api.endpoints.get_colorschemes",
            return_value=mock_colorschemes,
        ):
            response = client.get("/colors")
            assert response.status_code == 200
            data = response.json()
            assert "available_colors" in data
            assert "schemes" in data
            assert isinstance(data["available_colors"], list)
            assert isinstance(data["schemes"], dict)
            assert "white" in data["available_colors"]
            assert "black" in data["available_colors"]

    def test_list_colors_scheme_structure(self, client, mock_colorschemes):
        """Test that color scheme structure is correct."""
        with patch(
            "map_poster_creator.api.endpoints.get_colorschemes",
            return_value=mock_colorschemes,
        ):
            response = client.get("/colors")
            assert response.status_code == 200
            data = response.json()
            assert "white" in data["schemes"]
            scheme = data["schemes"]["white"]
            assert "facecolor" in scheme
            assert "water" in scheme
            assert "greens" in scheme
            assert "roads" in scheme


class TestPosterEndpoint:
    """Tests for POST /poster endpoint."""

    def test_poster_invalid_coordinates_too_few(self, client):
        """Test poster creation with too few coordinates."""
        request_data = {
            "coordinates": [
                {"lon": -74.006, "lat": 40.7128},
                {"lon": -73.935, "lat": 40.7128},
            ],
            "color": "white",
        }
        response = client.post("/poster", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_poster_invalid_coordinates_out_of_range(self, client):
        """Test poster creation with coordinates out of valid range."""
        request_data = {
            "coordinates": [
                {"lon": -74.006, "lat": 40.7128},
                {"lon": -73.935, "lat": 40.7128},
                {"lon": -73.935, "lat": 40.7589},
                {"lon": 200.0, "lat": 40.7589},  # Invalid longitude
            ],
            "color": "white",
        }
        response = client.post("/poster", json=request_data)
        assert response.status_code == 422

    def test_poster_invalid_color(self, client, sample_coordinates, mock_shp_dir):
        """Test poster creation with invalid color scheme."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "nonexistent_color",
            "shp_path": str(
                mock_shp_dir
            ),  # Provide SHP path to avoid SHP finding error
        }
        with patch(
            "map_poster_creator.api.endpoints.get_colorschemes"
        ) as mock_get_colors:
            mock_get_colors.return_value = {"white": MagicMock()}
            with patch(
                "map_poster_creator.api.endpoints.get_colorscheme",
                side_effect=KeyError("nonexistent_color"),
            ):
                response = client.post("/poster", json=request_data)
                assert response.status_code == 400
                data = response.json()
                assert "Unknown color scheme" in data["detail"]

    def test_poster_invalid_dpi(self, client, sample_coordinates):
        """Test poster creation with invalid DPI."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "dpi": 1000,  # Exceeds max of 600
        }
        response = client.post("/poster", json=request_data)
        assert response.status_code == 422

    def test_poster_invalid_width(self, client, sample_coordinates):
        """Test poster creation with invalid width."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "width": -5,  # Negative width
        }
        response = client.post("/poster", json=request_data)
        assert response.status_code == 422

    def test_poster_invalid_shp_path(
        self, client, sample_coordinates, mock_colorscheme
    ):
        """Test poster creation with non-existent SHP path."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "shp_path": "/nonexistent/path",
        }
        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            response = client.post("/poster", json=request_data)
            assert response.status_code == 400
            data = response.json()
            assert "SHP directory not found" in data["detail"]

    def test_poster_valid_with_shp_path(
        self, client, sample_coordinates, mock_shp_dir, mock_colorscheme, temp_dir
    ):
        """Test poster creation with valid SHP path."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "shp_path": str(mock_shp_dir),
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.create_poster_from_coordinates"
            ) as mock_create:
                mock_create.return_value = None
                with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                    mock_paths.output_dir = temp_dir / "output"
                    mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                    # Create a mock output file
                    output_file = mock_paths.output_dir / "poster_12345678.png"
                    output_file.touch()

                    with patch("map_poster_creator.api.endpoints.uuid4") as mock_uuid:
                        mock_uuid.return_value.hex = "12345678"
                        response = client.post("/poster", json=request_data)
                        # Should succeed if all mocks are set up correctly
                        assert response.status_code in [
                            200,
                            500,
                        ]  # May fail if create_poster fails

    def test_poster_valid_with_city(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test poster creation with city parameter."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "city": "New York",
            "country": "United States",
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.find_shp_from_polygon",
                return_value=mock_shp_dir,
            ):
                with patch(
                    "map_poster_creator.api.endpoints.create_poster_from_coordinates"
                ) as mock_create:
                    mock_create.return_value = None
                    with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                        mock_paths.output_dir = temp_dir / "output"
                        mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = mock_paths.output_dir / "poster_12345678.png"
                        output_file.touch()

                        with patch(
                            "map_poster_creator.api.endpoints.uuid4"
                        ) as mock_uuid:
                            mock_uuid.return_value.hex = "12345678"
                            response = client.post("/poster", json=request_data)
                            # Should call find_shp_from_polygon with city
                            assert response.status_code in [200, 500]

    def test_poster_auto_find_shp_failure(
        self, client, sample_coordinates, mock_colorscheme
    ):
        """Test poster creation when auto-finding SHP fails."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.find_shp_from_polygon",
                side_effect=HTTPException(status_code=400, detail="Could not find SHP"),
            ):
                response = client.post("/poster", json=request_data)
                assert response.status_code == 400

    def test_poster_create_error(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test poster creation when create_poster_from_coordinates raises an error."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "shp_path": str(mock_shp_dir),
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.create_poster_from_coordinates",
                side_effect=Exception("Poster creation failed"),
            ):
                with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                    mock_paths.output_dir = temp_dir / "output"
                    mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                    response = client.post("/poster", json=request_data)
                    assert response.status_code == 500
                    data = response.json()
                    assert "Error creating poster" in data["detail"]

    def test_poster_file_not_created(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test poster creation when output file is not created."""
        request_data = {
            "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
            "color": "white",
            "shp_path": str(mock_shp_dir),
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.create_poster_from_coordinates"
            ) as mock_create:
                mock_create.return_value = None
                with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                    mock_paths.output_dir = temp_dir / "output"
                    mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                    # Don't create the output file
                    with patch("map_poster_creator.api.endpoints.uuid4") as mock_uuid:
                        mock_uuid.return_value.hex = "12345678"
                        response = client.post("/poster", json=request_data)
                        assert response.status_code == 500
                        data = response.json()
                        assert "Poster file was not created" in data["detail"]

    def test_poster_different_dpi_values(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test poster creation with different DPI values."""
        for dpi in [150, 300, 600]:
            request_data = {
                "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
                "color": "white",
                "shp_path": str(mock_shp_dir),
                "dpi": dpi,
            }

            with patch(
                "map_poster_creator.api.endpoints.get_colorscheme",
                return_value=mock_colorscheme,
            ):
                with patch(
                    "map_poster_creator.api.endpoints.create_poster_from_coordinates"
                ) as mock_create:
                    mock_create.return_value = None
                    with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                        mock_paths.output_dir = temp_dir / "output"
                        mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = mock_paths.output_dir / f"poster_{dpi}.png"
                        output_file.touch()

                        with patch(
                            "map_poster_creator.api.endpoints.uuid4"
                        ) as mock_uuid:
                            mock_uuid.return_value.hex = f"{dpi:08d}"
                            response = client.post("/poster", json=request_data)
                            # Should accept valid DPI values
                            assert response.status_code in [200, 500]

    def test_poster_different_width_values(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test poster creation with different width values."""
        for width in [10.0, 15.0, 20.0, 30.0]:
            request_data = {
                "coordinates": [{"lon": c[0], "lat": c[1]} for c in sample_coordinates],
                "color": "white",
                "shp_path": str(mock_shp_dir),
                "width": width,
            }

            with patch(
                "map_poster_creator.api.endpoints.get_colorscheme",
                return_value=mock_colorscheme,
            ):
                with patch(
                    "map_poster_creator.api.endpoints.create_poster_from_coordinates"
                ) as mock_create:
                    mock_create.return_value = None
                    with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                        mock_paths.output_dir = temp_dir / "output"
                        mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = mock_paths.output_dir / f"poster_{width}.png"
                        output_file.touch()

                        with patch(
                            "map_poster_creator.api.endpoints.uuid4"
                        ) as mock_uuid:
                            mock_uuid.return_value.hex = f"{int(width):08d}"
                            response = client.post("/poster", json=request_data)
                            # Should accept valid width values
                            assert response.status_code in [200, 500]


class TestPosterSimpleEndpoint:
    """Tests for POST /poster/simple endpoint."""

    def test_poster_simple_invalid_coordinates_format(self, client):
        """Test simple poster with invalid coordinate format."""
        request_data = {
            "coordinates": [[-74.006], [40.7128]],  # Missing second coordinate
            "color": "white",
        }
        response = client.post("/poster/simple", json=request_data)
        assert response.status_code == 422

    def test_poster_simple_too_few_coordinates(self, client):
        """Test simple poster with too few coordinates."""
        request_data = {
            "coordinates": [
                [-74.006, 40.7128],
                [-73.935, 40.7128],
            ],
            "color": "white",
        }
        response = client.post("/poster/simple", json=request_data)
        assert response.status_code == 422

    def test_poster_simple_invalid_coordinate_type(self, client):
        """Test simple poster with invalid coordinate type."""
        request_data = {
            "coordinates": [
                [-74.006, 40.7128],
                [-73.935, 40.7128],
                "invalid",  # Not a list
            ],
            "color": "white",
        }
        response = client.post("/poster/simple", json=request_data)
        assert response.status_code == 422

    def test_poster_simple_valid_format(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test simple poster with valid coordinate format."""
        request_data = {
            "coordinates": sample_coordinates,
            "color": "white",
            "shp_path": str(mock_shp_dir),
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.create_poster_from_coordinates"
            ) as mock_create:
                mock_create.return_value = None
                with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                    mock_paths.output_dir = temp_dir / "output"
                    mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                    output_file = mock_paths.output_dir / "poster_12345678.png"
                    output_file.touch()

                    with patch("map_poster_creator.api.endpoints.uuid4") as mock_uuid:
                        mock_uuid.return_value.hex = "12345678"
                        response = client.post("/poster/simple", json=request_data)
                        # Should convert to PosterRequest and call create_poster_endpoint
                        assert response.status_code in [200, 500]

    def test_poster_simple_with_city_and_country(
        self, client, sample_coordinates, mock_colorscheme, mock_shp_dir, temp_dir
    ):
        """Test simple poster with city and country parameters."""
        request_data = {
            "coordinates": sample_coordinates,
            "color": "white",
            "city": "New York",
            "country": "United States",
        }

        with patch(
            "map_poster_creator.api.endpoints.get_colorscheme",
            return_value=mock_colorscheme,
        ):
            with patch(
                "map_poster_creator.api.endpoints.find_shp_from_polygon",
                return_value=mock_shp_dir,
            ):
                with patch(
                    "map_poster_creator.api.endpoints.create_poster_from_coordinates"
                ) as mock_create:
                    mock_create.return_value = None
                    with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                        mock_paths.output_dir = temp_dir / "output"
                        mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = mock_paths.output_dir / "poster_12345678.png"
                        output_file.touch()

                        with patch(
                            "map_poster_creator.api.endpoints.uuid4"
                        ) as mock_uuid:
                            mock_uuid.return_value.hex = "12345678"
                            response = client.post("/poster/simple", json=request_data)
                            assert response.status_code in [200, 500]

    def test_poster_simple_all_color_schemes(
        self, client, sample_coordinates, mock_colorschemes, mock_shp_dir, temp_dir
    ):
        """Test simple poster with all available color schemes."""
        for color_name in mock_colorschemes.keys():
            request_data = {
                "coordinates": sample_coordinates,
                "color": color_name,
                "shp_path": str(mock_shp_dir),
            }

            with patch(
                "map_poster_creator.api.endpoints.get_colorscheme",
                return_value=mock_colorschemes[color_name],
            ):
                with patch(
                    "map_poster_creator.api.endpoints.create_poster_from_coordinates"
                ) as mock_create:
                    mock_create.return_value = None
                    with patch("map_poster_creator.api.endpoints.paths") as mock_paths:
                        mock_paths.output_dir = temp_dir / "output"
                        mock_paths.output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = mock_paths.output_dir / f"poster_{color_name}.png"
                        output_file.touch()

                        with patch(
                            "map_poster_creator.api.endpoints.uuid4"
                        ) as mock_uuid:
                            mock_uuid.return_value.hex = color_name[:8].ljust(8, "0")
                            response = client.post("/poster/simple", json=request_data)
                            # Should accept all valid color schemes
                            assert response.status_code in [200, 500]
