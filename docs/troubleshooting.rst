Troubleshooting
===============

City commands fail before rendering
-----------------------------------

City-driven poster creation requires generated files under ``data_dir``,
including country data, GeoNames city data, geoBoundaries, and the Geofabrik
region tree. Run full ``scripts/setup.sh`` as described in
:doc:`data-sources`. Tiny setup intentionally omits the city and boundary
datasets. As an alternative, provide both ``--shp-path`` and
``--geojson-path`` without a positional city.

Colour commands fail with a missing file
----------------------------------------

The colour loader reads both ``colors.json`` and ``docc_colors.json``. The
former is created automatically on first colour-module import, but the latter
is not bundled and is currently opened even when only built-in colours are
requested. Run ``python scripts/fetch_docc_colors.py`` to generate it, or make
the generated colour library available at the configured data path.

GeoJSON is rejected
-------------------

Use a FeatureCollection with at least one Feature whose geometry type is
``Polygon`` or ``MultiPolygon``. Only the first Feature is used. Polygon
interior rings are ignored; for MultiPolygon input, the exterior ring of each
member polygon is used.

Rendering fails after inputs are accepted
-----------------------------------------

Confirm the shapefile directory directly contains the three expected files
listed in :doc:`quickstart`, and that the boundary overlaps their region.
Geometries touching but not strictly inside the boundary may be excluded.
Also check that the roads layer contains numeric ``maxspeed`` values, because
those values determine line widths.

Native dependency installation fails
------------------------------------

GeoPandas and related libraries rely on native geospatial components.
Install the system prerequisites in :doc:`installation`, then use an isolated
Python environment with compatible package versions. A NumPy ABI mismatch
between installed NumPy and Matplotlib/SciPy wheels is an environment issue;
reinstall compatible binary wheels or use a supported environment rather than
changing poster source data.

Configuration import fails after adding paths
---------------------------------------------

The configuration loader converts YAML path strings and creates the effective
directories at import time. Verify that ``data_dir``, ``output_dir``,
``MAPOC_DATA_DIR``, and ``MAPOC_OUTPUT_DIR`` identify writable locations.
Environment variables take precedence over YAML. See :doc:`configuration`.

Service remains in ``starting`` state
-------------------------------------

``GET /health`` returns HTTP 200 even when ``data_ready`` is false. Confirm
that ``geofabrik_tree.nw`` and ``geofabrik_urls.json`` exist in
``MAPOC_DATA_DIR`` and that the tree file is complete. The service waits up to
30 seconds during its background validation. Inspect
``<LOG_DIR>/map_poster_api.log`` for parsing or path errors.

Container is unhealthy or exits during startup
-----------------------------------------------

The entrypoint requires ``geofabrik_tree.nw`` to be at least 100 KB. An empty
or partially copied mounted file is rejected. Remove the incomplete data,
regenerate it with ``scripts/setup.sh``, and verify that the mounted
``MAPOC_DATA_DIR`` is writable. See :doc:`containerization` for source
precedence.

An unmodified checkout also cannot currently build the image because the
Dockerfile references a missing root ``requirements.txt``. This is an
implementation issue, not a Docker cache problem.

API cannot select a shapefile region
------------------------------------

Pass an existing server-side ``shp_path`` to bypass selection. Otherwise,
provide both ``latitude`` and ``longitude``, a resolvable city and country, or
coordinates whose centroid lies within the generated Geofabrik polygons.
City lookup requires full setup; tiny data supports point/centroid lookup
only. See :doc:`service`.
