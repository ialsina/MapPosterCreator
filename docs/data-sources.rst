Data sources and maintenance scripts
====================================

Map Poster Creator combines a user-supplied boundary with OpenStreetMap
shapefiles. City-driven commands additionally depend on local indexes created
by scripts in ``scripts/``.

Runtime sources
---------------

GeoJSON boundary
  A Polygon or MultiPolygon FeatureCollection supplied by the user, or a
  polygon constructed from coordinate pairs.

Geofabrik
  `Geofabrik <https://download.geofabrik.de/>`_ distributes the
  ``*-latest-free.shp.zip`` extracts used to render roads, water, and green
  areas. The application can choose a region by comparing the city point with
  cached region polygons and download its archive.

GeoNames
  `GeoNames cities1000 <https://download.geonames.org/export/dump/cities1000.zip>`_
  supplies city names, alternate names, countries, populations, and
  coordinates used for city resolution.

Country list
  The ``datasets/country-list`` CSV is used to map GeoNames country codes to
  country names.

geoBoundaries
  The ``geoBoundariesCGAZ_ADM2.geojson`` data set supplies administrative
  boundaries for the default city-driven CLI workflow. Matching first uses
  the resolved city's point and then falls back to name-based filtering.

Bootstrap local indexes
-----------------------

Run the setup orchestrator from the repository root after installing the
package:

.. code-block:: bash

   bash scripts/setup.sh

Full setup runs:

1. ``create_geonames_headers.py``
2. ``fetch_countries.py``
3. ``fetch_data_geonames.py``
4. ``build_region_tree.py``
5. ``fetch_geoboundaries.py``
6. optional ``fetch_docc_colors.py``

The first step now generates the GeoNames column-definition file required by
the third step. The region-tree script crawls Geofabrik pages and downloads
``.poly`` boundaries. The geoBoundaries file is large. Full setup can
therefore take several minutes and requires network access.

Setup options
-------------

.. code-block:: text

   scripts/setup.sh [--tiny] [--skip-colors] [--non-interactive]
                    [--output DIR]

``--tiny``
  Build only the Geofabrik region tree and, unless skipped, colour schemes.
  This is sufficient for coordinate-based region selection, but city lookup
  and automatic city boundaries are unavailable.

``--skip-colors``
  Do not fetch the Dictionary of Colour Combinations library. Although these
  schemes are conceptually optional, the current loader opens
  ``docc_colors.json`` unconditionally; colour listing and rendering fail
  when it is absent.

``--non-interactive``
  Continue without prompts and skip optional colours during full setup.

``--output DIR``
  Write generated files to this directory. It takes precedence over
  ``MAPOC_DATA_DIR``; otherwise the configured data directory defaults to
  ``~/.mapoc``.

The Docker image invokes tiny, non-interactive setup with ``--skip-colors`` by
default when no prepared data is available. ``NO_TINY=true`` selects the full
geographic setup but still skips colours. Supply prepared data containing
``docc_colors.json`` for poster operation and see :doc:`containerization`.

Generated files
---------------

Full setup produces:

* ``geonames_headers.txt`` and ``cities_geonames_1000.csv`` for city lookup;
* ``countries.csv`` for country name/code resolution;
* ``geofabrik_tree.nw``, ``geofabrik_tree.txt``, and
  ``geofabrik_urls.json`` for region selection and downloads;
* ``geoBoundariesCGAZ_ADM2.geojson`` for automatic city boundaries;
* optionally, ``docc_colors.json``.

``fetch_data_gh_datasets.py`` optionally fetches an alternative world-cities
CSV and records a commit hash. It is not consulted by the current city
resolution path, which uses the GeoNames CSV.

Colour-library generation
-------------------------

.. code-block:: bash

   python scripts/fetch_docc_colors.py

This retrieves the colour data used by the `Dictionary of Colour Combinations
<https://github.com/mattdesl/dictionary-of-colour-combinations>`_ project,
generates light and dark map schemes, and writes ``docc_colors.json`` into the
data directory. Generated scheme names begin with ``~docc-`` and encode the
book combination number, theme, and possible variant.

Supporting and legacy script
----------------------------

``scripts/match_cities.py`` is a standalone long-running analysis script that
matches every GeoNames city with Geofabrik region polygons and writes
``city_regions.json`` in the current working directory. The runtime does not
read that file; it is useful for offline investigation rather than normal
poster generation.

Network and source changes
--------------------------

These scripts depend on third-party URLs and their data formats. A source
change, failed request, or unavailable network can leave required files absent
or stale. When automation is unreliable, download the inputs manually and use
the explicit-path poster workflow in :doc:`quickstart`.
