# Map Poster Creator

Create minimalist road-map posters from OpenStreetMap data. Map Poster Creator
combines a GeoJSON boundary with a Geofabrik shapefile extract, then renders
roads, water, and green-area layers as a PNG with a chosen colour scheme.

This repository is a fork of
[k4m454k/MapPosterCreator](https://github.com/k4m454k/MapPosterCreator). It is
distributed under the [MIT License](LICENSE).

![Coral map poster](pics/msk_coral.png)

## Requirements

Use Python 3.10 or newer. Although older package metadata declared Python 3.7,
the current source uses Python 3.10 union-type syntax.

The GeoPandas stack may require native geospatial libraries:

- Debian/Ubuntu: `sudo apt-get install libgeos-dev`
- macOS: `brew install geos`
- Windows: install compatible GDAL/Fiona wheels if pip cannot install their
  native dependencies.

## Install

From a checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Verify the command-line interface:

```bash
mapoc --version
mapoc --help
```

## Create a poster

The current CLI uses a required city argument. With generated city metadata
available, it can open geojson.io for boundary creation and automatically
download the appropriate Geofabrik extract:

```bash
mapoc poster "Moscow, Russia" --colors white black --width 20cm --dpi 300
```

To use already downloaded inputs, supply both paths. The positional city
argument remains required, but is not resolved when both explicit paths are
provided:

```bash
mapoc poster "Berlin, Germany" \
  --shp-path /data/germany-latest-free \
  --geojson-path /data/berlin-boundary.geojson \
  --colors coral \
  --output-prefix berlin
```

The shapefile directory must directly contain:

- `gis_osm_roads_free_1.shp`
- `gis_osm_water_a_free_1.shp`
- `gis_osm_pois_a_free_1.shp`

The GeoJSON file must contain at least one `Feature` with `Polygon` geometry.
Only the first feature and its first exterior ring are used. Generated posters
are written to `~/mapoc` by default.

## Colour schemes

The built-in schemes are `black`, `white`, `red`, and `coral`.

```bash
mapoc color list
mapoc color show coral
mapoc color add coffee \
  --facecolor "#433633" \
  --water "#5c5552" \
  --greens "#8f857d" \
  --roads "#decbb7"
```

`browse` commands open the source sites in a browser:

```bash
mapoc browse shp
mapoc browse geojson
```

## City-data setup

City-driven downloads require locally generated country, GeoNames, and
Geofabrik index data. The maintenance scripts are:

```bash
python scripts/fetch_countries.py
python scripts/fetch_data_geonames.py
python scripts/build_region_tree.py
```

`fetch_data_geonames.py` additionally needs
`~/.mapoc/geonames_headers.txt`, which is not included in this repository.
Until the required local indexes are available, use the explicit-input
workflow above.

The extended Dictionary of Colour Combinations palette library is generated
separately:

```bash
python scripts/fetch_docc_colors.py
```

## Documentation

The complete Sphinx documentation covers configuration, data sources,
troubleshooting, architecture, and the programmatic API.

```bash
pip install -r docs/requirements.txt
make -C docs html
```

Open `docs/_build/html/index.html` after a successful build.
