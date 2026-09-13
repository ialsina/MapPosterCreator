Data sources and maintenance scripts
====================================

Map Poster Creator combines a user-supplied boundary with OpenStreetMap
shapefiles. City-driven commands additionally depend on local indexes created
by scripts in ``scripts/``.

Runtime sources
---------------

GeoJSON boundary
  A polygon FeatureCollection created by the user. During interactive use the
  application opens geojson.io centred on the resolved city, then opens a
  temporary text editor so the GeoJSON can be pasted into the created file.

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

Bootstrap local indexes
-----------------------

Run these from the repository root after installing the package dependencies:

.. code-block:: bash

   python scripts/fetch_countries.py
   python scripts/fetch_data_geonames.py
   python scripts/build_region_tree.py

They respectively create ``countries.csv``, the normalized GeoNames city CSV,
and Geofabrik's region tree/URLs beneath the configured data directory. The
region-tree script crawls Geofabrik pages and downloads ``.poly`` region
boundaries, so it can take time and requires network access.

The GeoNames script reads ``<data_dir>/geonames_headers.txt`` to name the
tab-separated fields, but that file is not included in this repository. It
will fail until a compatible GeoNames column-definition file is supplied at
that path. This makes automatic city lookup unavailable from a clean checkout
without additional setup. The explicit-input workflow remains usable without
these indexes.

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
