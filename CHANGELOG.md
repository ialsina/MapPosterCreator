# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [0.11.0] - 2026-09-18

### Added

- `docker-compose.yml` for local service deployment with host bind mounts for
  data, output, and logs.
- Environment-variable overrides `MAPOC_KEEP_SHP_FILES` and
  `MAPOC_KEEP_GEOJSON_FILES` for retaining on-request GeoFabrik shapefile and
  GeoJSON downloads under the data directory.
- Docker Compose `.env.example` and placeholder `.gitignore` files for
  `data/`, `output/`, and `logs/`.

### Changed

- Docker images now default `MAPOC_KEEP_SHP_FILES=true` so GeoFabrik SHP
  extracts persist under `/app/data/shp` instead of the temporary directory.
- The runtime entrypoint pre-creates `shp/` and `geojson/` directories under
  the effective data directory before starting Uvicorn.

## [0.10.0] - 2026-09-13

### Added

- FastAPI service with root, health, colour-listing, and poster-rendering
  endpoints.
- Poster creation directly from coordinate pairs through the Python API, CLI,
  and HTTP service.
- CLI options for coordinate files, country codes, and interactive city and
  region selection.
- Polygon and MultiPolygon support in the geometry and rendering pipeline.
- Automatic city-boundary lookup using geoBoundaries data.
- Automated full and tiny data-setup modes, including GeoNames headers,
  country/city data, Geofabrik indexes, geoBoundaries, and generated colour
  schemes.
- Docker image, runtime data entrypoint, environment-based paths, service
  logging, and data-aware health check.
- Pytest unit and integration suites, curl-based API tests, fixtures, examples,
  and coverage configuration.
- Sphinx documentation for installation, configuration, data sources, CLI,
  HTTP service, containerization, architecture, troubleshooting, and the
  Python API.
- Modern `pyproject.toml` packaging and development-tool configuration.

### Changed

- Moved the installable package to a `src/` layout.
- Split the former data module into focused models, getters, geometry,
  interactive, and utility modules.
- Added cached data models and more robust region-tree loading and validation.
- Improved Geofabrik region selection to operate on leaf regions and support
  direct point lookup.
- Improved plotting behavior for empty layers, invalid bounds, and aspect-ratio
  failures.
- Added environment-variable precedence for data and output directories.
- Pinned the core scientific and geospatial dependency ranges.
- Moved project images from `pics/` to `assets/`.
- Expanded and reorganized the README around current CLI, service, setup, and
  container workflows.

### Fixed

- Corrected coordinate serialization and added output-directory creation.
- Corrected geoBoundaries setup and lookup behavior.
- Preserved Geofabrik download URLs discovered outside HTML tables.
- Improved build-time and runtime data copying and incomplete-tree detection.
- Improved errors when full-data features are used with a tiny installation.
- Corrected configuration-root and local API log locations after the `src/`
  layout migration.
- Improved test isolation and performance.
- Aligned the Dockerfile with `pyproject.toml` instead of a missing root
  `requirements.txt`.
- Docker build and entrypoint now generate `docc_colors.json` via
  `scripts/fetch_docc_colors.py` instead of skipping colour setup.

### Known issues

- CLI coordinate-file mode without `--output-prefix` attempts to convert a
  Shapely Polygon to `Path`.
- Some generated Geofabrik leaf regions have no supported shapefile archive,
  causing automatic downloads to fail for those locations.
- Rendering uses strict geometric containment, which omits features crossing
  the requested boundary.

## [0.9.0] - 2024-07-19

### Added

- City and country data download scripts backed by GeoNames and the country
  list dataset.
- Interactive GeoJSON creation and Geofabrik shapefile acquisition.
- Automatic Geofabrik region discovery, download, extraction, and reuse.
- Configurable output directory, poster width, and DPI.
- `mapoc poster`, browsing helpers, and colour-management commands.
- Built-in Matplotlib colour-name support and palette previews.
- Procedurally generated light and dark schemes based on *A Dictionary of
  Colour Combinations*.
- Tabular, sorted colour-scheme listing.

### Changed

- Improved city resolution across ASCII names, localized names, alternate
  names, population ordering, and intermediate administrative codes.
- Selected the first region that actually contains a city rather than relying
  only on nearest-centroid distance.
- Made the city argument positional and allowed temporary GeoJSON reuse.
- Refactored the command entry points, rendering core, and colour-scheme model.
