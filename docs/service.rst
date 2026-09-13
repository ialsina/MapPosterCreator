HTTP service
============

Map Poster Creator exposes a FastAPI service that accepts polygon coordinates
and returns rendered PNG files. It can run from an installed checkout or as
the default process in the Docker image.

Start locally
-------------

Install the package and prepare at least the tiny data set, including
``docc_colors.json``, as described in :doc:`data-sources`, then run:

.. code-block:: bash

   uvicorn map_poster_creator.api:app --host 0.0.0.0 --port 8000

The service is available at ``http://localhost:8000``. FastAPI publishes
interactive OpenAPI documentation at ``/docs`` and ReDoc at ``/redoc``.
Container startup and its current build limitation are covered in
:doc:`containerization`.

Configuration and logging
-------------------------

The service recognizes:

``MAPOC_DATA_DIR``
  Data and index directory. The local default is ``~/.mapoc`` and the image
  default is ``/app/data``.

``MAPOC_OUTPUT_DIR``
  Directory for generated server-side PNG files. The local default is
  ``~/mapoc`` and the image default is ``/app/output``.

``LOG_DIR``
  Directory containing ``map_poster_api.log``. It defaults to ``/app/logs``,
  even when the service is launched outside the image.

``LOG_LEVEL``
  Console logging level, defaulting to ``INFO``. The file handler records
  ``DEBUG`` and higher.

The log and configured data/output directories are created during import.
Ensure the service account can write to them.

Startup and readiness
---------------------

Startup schedules a background check for ``geofabrik_tree.nw`` and
``geofabrik_urls.json``. For up to 30 seconds it waits for both files and
validates the region tree. Startup itself is not blocked.

``GET /health`` reports:

* ``status: healthy`` and ``data_ready: true`` when the tree can be loaded;
* ``status: starting`` and ``data_ready: false`` while data is unavailable;
* ``regions_tree_nodes`` when validation succeeds.

The health route returns HTTP 200 in both states. Readiness checks must test
the ``data_ready`` field. It does not validate colour files or shapefile
downloads, so a ready service can still reject poster work when those
resources are missing.

Endpoints
---------

``GET /``
  Return service metadata and route names.

``GET /health``
  Return liveness and data-readiness details.

``GET /colors``
  Return all available colour-scheme names and their component colours.

``POST /poster``
  Accept coordinate objects and return a PNG.

``POST /poster/simple``
  Accept the same request with coordinates represented as arrays.

The service has no ``/poster/json`` route.

Create a poster
---------------

The main request uses at least three longitude/latitude objects:

.. code-block:: bash

   curl -X POST http://localhost:8000/poster \
     -H "Content-Type: application/json" \
     -d '{
       "coordinates": [
         {"lon": 2.145, "lat": 41.375},
         {"lon": 2.190, "lat": 41.375},
         {"lon": 2.190, "lat": 41.410},
         {"lon": 2.145, "lat": 41.410}
       ],
       "color": "white",
       "width": 15.0,
       "dpi": 300
     }' \
     --output poster.png

``coordinates`` is required. The polygon is closed automatically. Longitude
must be between -180 and 180, latitude between -90 and 90, ``width`` must be
positive, and ``dpi`` must be between 1 and 600. Width is measured in inches.

Optional fields are:

* ``shp_path``: an existing server-side shapefile directory;
* ``latitude`` and ``longitude``: a point used to select a Geofabrik region;
* ``city`` and ``country``: location names used for region selection;
* ``color``: colour scheme name, default ``white``;
* ``width``: poster width in inches, default ``15.0``;
* ``dpi``: output resolution, default ``300``.

The simplified endpoint accepts ``[[longitude, latitude], ...]``:

.. code-block:: bash

   curl -X POST http://localhost:8000/poster/simple \
     -H "Content-Type: application/json" \
     -d '{
       "coordinates": [
         [2.145, 41.375],
         [2.190, 41.375],
         [2.190, 41.410],
         [2.145, 41.410]
       ],
       "color": "black"
     }' \
     --output poster.png

Shapefile selection
-------------------

When ``shp_path`` is absent, the service selects and downloads a Geofabrik
extract using this precedence:

1. an explicit ``latitude`` and ``longitude`` pair;
2. ``city`` and optional ``country``;
3. the submitted polygon's centroid.

Supplying only one of latitude or longitude does not activate point lookup.
Automatic selection requires a valid Geofabrik tree and URL index. City
selection additionally requires the full GeoNames/country data set.

Responses and errors
--------------------

Successful poster requests return ``image/png`` and use a download filename
based on the requested colour. A uniquely named server-side copy remains in
``MAPOC_OUTPUT_DIR``.

Request-model validation produces HTTP 422. Invalid SHP paths, unknown
colours, or failed automatic region selection produce HTTP 400. Rendering and
unexpected failures produce HTTP 500; consult ``map_poster_api.log`` for
detailed diagnostics.
