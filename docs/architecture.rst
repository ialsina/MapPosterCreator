Architecture
============

The package is a command-line application with a local data/cache layer and a
Matplotlib rendering pipeline.

Poster rendering flow
---------------------

1. ``mapoc`` invokes ``map_poster_creator.entrypoints.map_poster``.
2. The ``poster`` service obtains a GeoJSON boundary and shapefile directory:
   from command-line paths, or by resolving a city and running interactive
   browser/download workflows.
3. ``core.create_poster`` reads the boundary and the three expected shapefile
   layers with GeoPandas.
4. The preprocessing layer retains geometries strictly contained by the
   boundary. For roads, it drops ``footway`` and ``steps`` classes and copies
   each ``maxspeed`` to a ``speeds`` column.
5. ``plotting.plot_and_save`` draws water, greens, then roads with Matplotlib,
   applies the boundary extents and a latitude-derived aspect ratio, hides
   axes, and writes the PNG.

Modules
-------

``entrypoints``
  Defines the ``argparse`` command tree and command services.

``data``
  Resolves cities from local GeoNames data, manages interactive boundary
  capture, selects Geofabrik regions, and downloads/extracts shapefile
  archives.

``geojson``
  Validates a restricted GeoJSON shape and derives its bounding-box
  ``MapGeometry``.

``core``
  Coordinates layer loading, geometric filtering, and rendering.

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

Data boundaries
---------------

The renderer does not query OpenStreetMap directly. It reads a previously
downloaded Geofabrik extract. The application does query GeoNames and
Geofabrik indirectly through the maintenance scripts and automatic download
flow, so its city-driven convenience features depend on generated local files
and live external services.

Notable implementation constraints
----------------------------------

* Geometric filtering uses ``Polygon.contains``. Features touching the
  boundary are not retained by a strict contains test.
* Rendering assumes a usable numeric ``maxspeed`` field in the road layer.
  Missing or non-numeric values can prevent line-width calculation.
* The map is square: specifying width sets both figure dimensions.
* The aspect-ratio correction derives latitude from the boundary centre.
* Only the first GeoJSON Feature and its first coordinate ring are rendered.

These are current behavior constraints, not broad GeoJSON or OpenStreetMap
format guarantees.
