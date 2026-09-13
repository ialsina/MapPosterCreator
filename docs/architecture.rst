Architecture
============

The package has command-line and FastAPI interfaces over a shared local
data/cache layer and Matplotlib rendering pipeline.

Poster rendering flow
---------------------

1. The CLI or HTTP service obtains a Polygon/MultiPolygon boundary and
   shapefile directory. Boundaries may come from GeoJSON, coordinate pairs, or
   the local geoBoundaries data set.
2. Region selection uses an explicit path, coordinates, a resolved city, or
   a polygon centroid, then downloads the matching Geofabrik archive when
   required.
3. ``core.create_poster`` accepts a geometry object or reads the first Feature
   from a GeoJSON file, then loads the three expected shapefile layers with
   GeoPandas. ``create_poster_from_coordinates`` constructs the polygon first.
4. The preprocessing layer retains geometries strictly contained by the
   boundary. For roads, it drops ``footway`` and ``steps`` classes and copies
   each ``maxspeed`` to a ``speeds`` column.
5. ``plotting.plot_and_save`` draws water, greens, then roads with Matplotlib,
   applies the boundary extents and a latitude-derived aspect ratio, hides
   axes, and writes the PNG. Empty or invalid-bounds layers are skipped.

Service and container startup
-----------------------------

``map_poster_creator.api`` configures console/file logging, creates the
FastAPI application, registers routes, and schedules a non-blocking data
validation task. Poster routes use the same coordinate, region-selection, and
rendering functions as the CLI.

The Docker entrypoint prepares ``MAPOC_DATA_DIR`` before executing Uvicorn.
Build data is staged in ``/app/data_source``; mounted data or a runtime tiny
setup can also satisfy startup. The image health check treats the service as
ready only when ``GET /health`` reports ``data_ready``. See
:doc:`containerization` and :doc:`service`.

Modules
-------

``entrypoints``
  Defines the ``argparse`` command tree and command services.

``data``
  Package containing cached models/getters, city and region selection,
  interactive callbacks, and download/extraction utilities.

``geometry``
  Parses coordinates and Polygon/MultiPolygon GeoJSON, creates geometry
  files, and derives bounding-box ``MapGeometry`` values.

``core``
  Coordinates layer loading, geometric filtering, and rendering from files
  or in-memory polygons.

``plotting``
  Contains layer plotting, speed-to-line-width mapping, and PNG export.

``colorscheme``
  Defines colour values, serializes palette files, combines user and generated
  libraries, and exposes palette operations.

``config``
  Loads repository-level settings and defines paths for user data, output,
  caches, and indexes.

``logs``
  Provides the lightweight processing-log decorator used around selected
  expensive operations.

``api``
  Defines the FastAPI application, request models, endpoints, readiness
  checks, and shapefile auto-selection helpers.

Data boundaries
---------------

The renderer does not query OpenStreetMap directly. It reads a previously
downloaded Geofabrik extract. The application does query GeoNames and
Geofabrik indirectly through the maintenance scripts and automatic download
flow, so its convenience features depend on generated local files and live
external services. Full setup provides GeoNames, country, geoBoundaries, and
Geofabrik indexes. Tiny setup provides only the Geofabrik region data needed
for coordinate-based selection.

Notable implementation constraints
----------------------------------

* Geometric filtering uses ``Polygon.contains``. Features touching the
  boundary are not retained by a strict contains test.
* Rendering assumes a usable numeric ``maxspeed`` field in the road layer.
  Missing or non-numeric values can prevent line-width calculation.
* The map is square: specifying width sets both figure dimensions.
* The aspect-ratio correction derives latitude from the boundary centre.
* Only the first GeoJSON Feature is rendered. Polygon interior rings and
  MultiPolygon interior rings are ignored.

These are current behavior constraints, not broad GeoJSON or OpenStreetMap
format guarantees.
