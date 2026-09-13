Quickstart
==========

The fastest full-data workflow is to give ``mapoc`` a city name. It resolves
the city, obtains its administrative boundary from local geoBoundaries data,
finds a Geofabrik region, downloads the region's free shapefiles, and renders
a PNG.

.. code-block:: bash

   mapoc poster "Moscow, Russia" --colors white black --width 20cm --dpi 300

By default, an ambiguous city name selects the highest-population match. Add
``--interactive`` to choose from multiple matches, or ``--country-code`` to
narrow the lookup.
The default output prefix is the city text before the comma. Files are written
to the configured output directory (``~/mapoc`` by default), for example
``Moscow_white.png`` and ``Moscow_black.png``.

Explicit inputs
---------------

You can avoid lookup and download steps by providing both local inputs. The
city argument is optional when a boundary and shapefile directory are
provided:

.. code-block:: bash

   mapoc poster \
     --shp-path /data/germany-latest-free \
     --geojson-path /data/berlin-boundary.geojson \
     --colors coral \
     --output-prefix berlin

With a city plus either supplied path, ``mapoc`` obtains the missing input.
Without a city, an explicit ``--shp-path`` is required because the CLI cannot
select a Geofabrik region from a boundary alone.

Coordinates file
----------------

Instead of GeoJSON, provide a polygon as a JSON array, comma-separated rows,
or whitespace-separated rows. Each pair is longitude followed by latitude:

.. code-block:: bash

   mapoc poster \
     --coordinates-file boundary.json \
     --shp-path /data/germany-latest-free \
     --colors white black \
     --output-prefix berlin

For example, ``boundary.json`` can contain:

.. code-block:: json

   [[13.35, 52.48], [13.45, 52.48], [13.45, 52.55], [13.35, 52.55]]

At least three points are required and the polygon is closed automatically.
If a city is supplied, ``mapoc`` can use it to select the missing shapefile
directory. ``--coordinates-file`` and ``--geojson-path`` are mutually
exclusive.

Prepare a boundary
------------------

Create a Polygon or MultiPolygon in `geojson.io <https://geojson.io/>`_ or
another GeoJSON editor. The renderer accepts a FeatureCollection and uses its
first Feature. For a Polygon with multiple rings, only the first ring is used.
For a MultiPolygon, the exterior ring of each polygon is rendered; interior
rings are ignored.

Prepare OpenStreetMap data
--------------------------

Download a ``*-latest-free.shp.zip`` archive from
`Geofabrik <https://download.geofabrik.de/>`_ and extract it. The selected
directory must directly contain:

* ``gis_osm_roads_free_1.shp``
* ``gis_osm_water_a_free_1.shp``
* ``gis_osm_pois_a_free_1.shp``

The boundary must overlap the selected region's geometries. A boundary outside
the shapefiles can cause poster creation to fail.

What is rendered
----------------

Road features tagged as ``footway`` or ``steps`` are excluded. Road line
widths are based on each feature's ``maxspeed`` value. Water areas, points of
interest (used as green areas), and roads are layered in that order. See
:doc:`architecture` for the full pipeline.

To create posters over HTTP, continue with :doc:`service`.
