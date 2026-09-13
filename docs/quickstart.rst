Quickstart
==========

The fastest workflow is to give ``mapoc`` a city name. It locates the city,
opens a browser centred on it for boundary creation, finds a Geofabrik region,
downloads the region's free shapefiles, and renders a PNG.

.. code-block:: bash

   mapoc poster "Moscow, Russia" --colors white black --width 20cm --dpi 300

When more than one matching city exists, the command prompts you to select one.
The default output prefix is the city text before the comma. Files are written
to the configured output directory (``~/mapoc`` by default), for example
``Moscow_white.png`` and ``Moscow_black.png``.

Explicit inputs
---------------

You can avoid interactive browser and download steps by providing both required
local inputs. The current CLI still requires a positional city argument, but
when both paths are present it does not resolve that city or access its local
metadata:

.. code-block:: bash

   mapoc poster "Berlin, Germany" \
     --shp-path /data/germany-latest-free \
     --geojson-path /data/berlin-boundary.geojson \
     --colors coral \
     --output-prefix berlin

With a city plus either supplied path, ``mapoc`` obtains the missing input.
The positional argument cannot currently be omitted, even though the service
implementation contains a path-only branch.

Prepare a boundary
------------------

Create one polygon in `geojson.io <https://geojson.io/>`_ or another GeoJSON
editor. The renderer accepts a FeatureCollection and uses its first Feature,
which must have ``geometry.type`` set to ``Polygon``. If the polygon has
multiple rings, only the first ring is used. Multipolygons are not accepted.

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
