# Scripts Documentation

This directory contains setup and data fetching scripts for Map Poster Creator. These scripts download and prepare the necessary data files that the main application requires.

## Script Overview

### 1. `create_geonames_headers.py`
**Purpose**: Creates the `geonames_headers.txt` file required by `fetch_data_geonames.py` to parse GeoNames data format.

**Inputs**:
- None (generates file from standard GeoNames format)

**Outputs**:
- `~/.mapoc/geonames_headers.txt` - Column definitions for GeoNames cities1000.txt format

**Dependencies**:
- Required by `fetch_data_geonames.py` before it can process city data

**Usage**:
```bash
python scripts/create_geonames_headers.py
```

**Notes**:
- This file must exist before running `fetch_data_geonames.py`
- Based on the standard GeoNames format documentation

---

### 2. `fetch_geoboundaries.py`
**Purpose**: Downloads the geoBoundariesCGAZ_ADM2.geojson file containing administrative boundaries for cities and regions.

**Inputs**:
- None (fetches from GitHub: wmgeolab/geoBoundaries)

**Outputs**:
- `~/.mapoc/geoBoundariesCGAZ_ADM2.geojson` - Large GeoJSON file with administrative boundaries

**Dependencies**:
- Used by `map_poster_creator/data.py` via `get_geoboundaries_gdf()` function
- Required for automatic city boundary polygon generation

**Usage**:
```bash
python scripts/fetch_geoboundaries.py
```

**Notes**:
- This is a large file (several hundred MB) and download may take several minutes
- Shows download progress during fetch
- Prompts before overwriting existing file

---

### 3. `build_region_tree.py`
**Purpose**: Builds a hierarchical tree structure of geographic regions from GeoFabrik and fetches polygon boundary data for each region.

**Inputs**:
- None (fetches from `https://download.geofabrik.de/`)

**Outputs**:
- `~/.mapoc/geofabrik_tree.nw` - Newick format tree file containing region hierarchy
- `~/.mapoc/geofabrik_tree.txt` - Human-readable JSON tree structure
- `~/.mapoc/geofabrik_urls.json` - Mapping of region names to their download URLs

**Dependencies**:
- Used by `map_poster_creator/data.py` to find and download shapefile archives for regions
- Required for the `download_shp_interactive` functionality

**Usage**:
```bash
python scripts/build_region_tree.py
```

**Notes**:
- This script crawls the GeoFabrik website recursively
- Fetches `.poly` polygon files for each region
- Can take several minutes to complete due to network requests

---

### 4. `crawl_geofabrik.py` ⚠️ **DUPLICATE/UNUSED**
**Purpose**: Generic recursive web crawler for GeoFabrik website.

**Status**: **This script appears to be duplicated by `build_region_tree.py`** and is not used anywhere in the codebase. The `build_region_tree.py` script provides a more structured and complete solution for crawling GeoFabrik.

**Inputs**:
- Command-line arguments:
  - `--follow`: File extensions to follow recursively (default: `.html`, `.htm`)
  - `--extract`: File extensions to include in results (default: all)

**Outputs**:
- Prints extracted URLs to stdout

**Recommendation**: This script can be removed as `build_region_tree.py` provides the necessary functionality.

---

### 5. `fetch_countries.py`
**Purpose**: Downloads the country list dataset from GitHub.

**Inputs**:
- None (fetches from `https://raw.githubusercontent.com/datasets/country-list/master/data.csv`)

**Outputs**:
- `~/.mapoc/countries.csv` - CSV file with country codes and names

**Dependencies**:
- Used by `map_poster_creator/data.py` via `get_country_df()` function
- Required for country name/code resolution

**Usage**:
```bash
python scripts/fetch_countries.py
```

---

### 6. `fetch_data_geonames.py`
**Purpose**: Downloads and processes city data from GeoNames (cities with population > 1000).

**Inputs**:
- None (fetches from `https://download.geonames.org/export/dump/cities1000.zip`)
- Requires `~/.mapoc/geonames_headers.txt` file (not automatically created)

**Outputs**:
- `~/.mapoc/cities_geonames_1000.csv` - Processed CSV file with city data
- Temporary files (`.zip` and `.txt`) are cleaned up after processing

**Dependencies**:
- Used by `map_poster_creator/data.py` via `get_cities_geonames()` function
- Required for city lookup and geocoding functionality

**Usage**:
```bash
python scripts/fetch_data_geonames.py
```

**Notes**:
- Prompts user if the zip file already exists
- Requires `geonames_headers.txt` file to parse the GeoNames data format
- This file should contain column definitions (one per line, format: `column_name: description`)

---

### 7. `fetch_data_gh_datasets.py`
**Purpose**: Downloads city data from GitHub datasets repository (alternative to GeoNames).

**Inputs**:
- None (fetches from `https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv`)

**Outputs**:
- `~/.mapoc/cities_gh_datasets.csv` - CSV file with world cities data
- `~/.mapoc/.cities_gh_datasets.hash` - Hash file to track updates

**Dependencies**:
- Currently not directly used by the main application
- May be an alternative data source for city information

**Usage**:
```bash
python scripts/fetch_data_gh_datasets.py
```

**Notes**:
- Checks commit hash to avoid unnecessary re-downloads
- Falls back to existing file if download fails

---

### 8. `fetch_docc_colors.py`
**Purpose**: Fetches color combinations from "A Dictionary of Color Combinations" and generates color schemes.

**Inputs**:
- None (fetches from `https://raw.githubusercontent.com/mattdesl/dictionary-of-colour-combinations/master/colors.json`)

**Outputs**:
- `~/.mapoc/docc_colors.json` - JSON file containing generated color schemes

**Dependencies**:
- Used by `map_poster_creator/colorscheme.py` to provide additional color scheme options
- Color schemes are named with pattern: `~docc-XXX-theme-Y` where:
  - `XXX` is the combination number
  - `theme` is either "light" or "dark"
  - `Y` is an identifier for unique combinations (omitted if only one)

**Usage**:
```bash
python scripts/fetch_docc_colors.py
```

**Notes**:
- Generates multiple color scheme variations from each color combination
- Uses permutations to create light and dark themed variations
- Can take a while to process all combinations

---

### 9. `match_cities.py`
**Purpose**: Matches cities from GeoNames dataset to GeoFabrik regions using spatial intersection.

**Inputs**:
- `~/.mapoc/cities_geonames_1000.csv` (from `fetch_data_geonames.py`)
- `~/.mapoc/geofabrik_tree.nw` (from `build_region_tree.py`)
- `~/.mapoc/countries.csv` (from `fetch_countries.py`)

**Outputs**:
- `city_regions.json` - JSON file mapping city names to their corresponding GeoFabrik regions

**Dependencies**:
- Requires all three input files to be present
- This appears to be a utility script for building a city-to-region mapping

**Usage**:
```bash
python scripts/match_cities.py
```

**Notes**:
- Uses spatial intersection to determine which region contains each city
- Can be slow for large datasets
- Output file is created in the current working directory

---

### 10. `geoboundaries.py` ⚠️ **INCOMPLETE/TEST SCRIPT**
**Purpose**: Appears to be a test/development script for working with geoboundaries data.

**Status**: **This script is incomplete** - it contains module-level code that would execute on import. The actual geoboundaries functionality is implemented in `map_poster_creator/data.py`.

**Inputs**:
- `~/.mapoc/geoBoundariesCGAZ_ADM2.geojson` (must be manually downloaded)

**Outputs**:
- None (test script)

**Dependencies**:
- The geoboundaries GeoJSON file must be manually downloaded from the geoBoundaries project
- Used by `map_poster_creator/data.py` via `get_geoboundaries_gdf()` function

**Recommendation**: This script should be refactored or removed. Consider creating a proper download script for geoboundaries data.

---

## Data File Dependencies

The following data files are required by the main application:

| File | Source Script | Required? | Notes |
|------|--------------|-----------|-------|
| `geofabrik_tree.nw` | `build_region_tree.py` | Yes | For region lookup |
| `geofabrik_tree.txt` | `build_region_tree.py` | No | Human-readable version |
| `geofabrik_urls.json` | `build_region_tree.py` | Yes | For downloading shapefiles |
| `countries.csv` | `fetch_countries.py` | Yes | For country resolution |
| `cities_geonames_1000.csv` | `fetch_data_geonames.py` | Yes | For city lookup |
| `docc_colors.json` | `fetch_docc_colors.py` | No | Optional color schemes |
| `geoBoundariesCGAZ_ADM2.geojson` | `fetch_geoboundaries.py` | Yes | For city boundary polygons |
| `geonames_headers.txt` | `create_geonames_headers.py` | Yes | Required for parsing GeoNames data |
| `cities_gh_datasets.csv` | `fetch_data_gh_datasets.py` | No | Alternative city data |

## Setup Order

The recommended order for running setup scripts:

1. `create_geonames_headers.py` - Create headers file (required first)
2. `fetch_countries.py` - Basic country data
3. `fetch_data_geonames.py` - City data (requires `geonames_headers.txt`)
4. `build_region_tree.py` - Region hierarchy and URLs
5. `fetch_geoboundaries.py` - Administrative boundaries (large file)
6. `fetch_docc_colors.py` - Optional color schemes

See the main `README.md` and `scripts/setup.sh` for automated setup.
