# Map Poster Creator API

A FastAPI-based REST API for creating map posters from polygon coordinates.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the API server:

```bash
python -m map_poster_creator.api
```

Or using uvicorn directly:

```bash
uvicorn map_poster_creator.api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## Endpoints

### `GET /`
Root endpoint with API information.

### `GET /health`
Health check endpoint.

### `GET /colors`
List all available color schemes.

**Example:**
```bash
curl http://localhost:8000/colors
```

### `POST /poster`
Create a map poster from polygon coordinates.

**Request Body (JSON):**
```json
{
  "coordinates": [
    {"lon": -74.006, "lat": 40.7128},
    {"lon": -73.935, "lat": 40.7128},
    {"lon": -73.935, "lat": 40.7589},
    {"lon": -74.006, "lat": 40.7589}
  ],
  "city": "New York",
  "country": "United States",
  "color": "white",
  "width": 15.0,
  "dpi": 300
}
```

**Parameters:**
- `coordinates` (required): List of coordinate objects with `lon` and `lat` fields (minimum 3 points)
- `shp_path` (optional): Path to SHP directory. If not provided, will attempt to find automatically.
- `city` (optional): City name to help find the SHP region automatically.
- `country` (optional): Country name to help find the SHP region automatically.
- `color` (optional, default: "white"): Color scheme name. Use `/colors` endpoint to see available schemes.
- `width` (optional, default: 15.0): Width of the poster in inches.
- `dpi` (optional, default: 300): Dots per inch (resolution), max 600.

**Response:**
Returns a PNG image file.

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/poster" \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [
      {"lon": -74.006, "lat": 40.7128},
      {"lon": -73.935, "lat": 40.7128},
      {"lon": -73.935, "lat": 40.7589},
      {"lon": -74.006, "lat": 40.7589}
    ],
    "city": "New York",
    "color": "white",
    "width": 15.0,
    "dpi": 300
  }' \
  --output poster.png
```

### `POST /poster/json`
Alternative endpoint that accepts coordinates as a JSON array directly in query parameters.

**Example:**
```bash
curl -X POST "http://localhost:8000/poster/json?coordinates=[[-74.006,40.7128],[-73.935,40.7128],[-73.935,40.7589],[-74.006,40.7589]]&city=New%20York&color=white" \
  --output poster.png
```

## Python Client Example

```python
import requests

# API endpoint
url = "http://localhost:8000/poster"

# Request payload
payload = {
    "coordinates": [
        {"lon": -74.006, "lat": 40.7128},
        {"lon": -73.935, "lat": 40.7128},
        {"lon": -73.935, "lat": 40.7589},
        {"lon": -74.006, "lat": 40.7589}
    ],
    "city": "New York",
    "color": "white",
    "width": 15.0,
    "dpi": 300
}

# Make request
response = requests.post(url, json=payload)

# Save the image
if response.status_code == 200:
    with open("poster.png", "wb") as f:
        f.write(response.content)
    print("Poster saved to poster.png")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

## Notes

- Coordinates should be provided as `[longitude, latitude]` pairs (not lat/lon).
- The polygon will be automatically closed if the first and last points don't match.
- If `shp_path` is not provided, the API will attempt to automatically determine the region from the polygon's centroid or the provided city name.
- The SHP files may need to be downloaded on first use, which can take some time.

