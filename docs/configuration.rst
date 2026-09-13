Configuration and local files
=============================

Repository configuration
------------------------

``config.yaml`` at the repository root is read when
``map_poster_creator.config`` is imported. It accepts the fields of
``Config``:

.. code-block:: yaml

   data_dir: /path/to/mapoc-data
   output_dir: /path/to/posters
   default_width: 15cm
   default_dpi: 300
   keep_shp_files: false
   keep_geojson_files: false

The tracked configuration file is empty, so built-in defaults apply:

* ``data_dir``: ``~/.mapoc``
* ``output_dir``: ``~/mapoc``
* ``default_width``: ``15cm``
* ``default_dpi``: ``300``
* ``keep_shp_files`` and ``keep_geojson_files``: ``false``

YAML strings for ``data_dir`` and ``output_dir`` are converted to
``pathlib.Path`` values. ``~`` in configured paths is expanded and relative
paths are resolved when the effective directories are computed. Both
directories are created during module import.

Environment variables
---------------------

``MAPOC_DATA_DIR`` and ``MAPOC_OUTPUT_DIR`` override their corresponding YAML
values and defaults. They are intended for service and container deployments:

.. code-block:: bash

   export MAPOC_DATA_DIR=/srv/mapoc/data
   export MAPOC_OUTPUT_DIR=/srv/mapoc/output

The Docker image sets them to ``/app/data`` and ``/app/output``. The FastAPI
service additionally recognizes ``LOG_DIR`` (default ``/app/logs``) and
``LOG_LEVEL`` (default ``INFO``); see :doc:`service`.

Generated and cached data
-------------------------

The application keeps city metadata, country metadata, Geofabrik hierarchy
data, generated colour schemes, and optional retained downloads below
``data_dir``. The following files are relevant to normal city-driven poster
creation:

* ``countries.csv``
* ``cities_geonames_1000.csv``
* ``geofabrik_tree.nw``
* ``geofabrik_urls.json``
* ``geoBoundariesCGAZ_ADM2.geojson``
* ``geonames_headers.txt``
* ``docc_colors.json``
* ``colors.json``

The source repository does not bundle these generated files. Populate them
using the maintenance scripts described in :doc:`data-sources` before relying
on city lookup and automatic Geofabrik selection.

Transient versus retained input
-------------------------------

By default, interactive GeoJSON files and automatically downloaded shapefile
archives are placed below the operating system temporary directory in
``mapoc/geojson`` and ``mapoc/shp``. Set the corresponding ``keep_*`` option
to ``true`` to store them below ``data_dir`` instead. Reusing cached inputs
may avoid another edit or download, but does not validate that they still match
the desired city or source data.

Colour configuration
--------------------

On first import of the colour module, Map Poster Creator creates
``<data_dir>/colors.json`` with the built-in schemes when it is missing. User
schemes saved by ``mapoc color add`` are kept there. The runtime also loads
``docc_colors.json`` from ``data_dir``; create it with
``scripts/fetch_docc_colors.py`` if you want the generated Dictionary of
Colour Combinations library.

Container paths and volumes
---------------------------

Container data may be baked into ``/app/data_source`` and copied to the
effective ``MAPOC_DATA_DIR`` by the entrypoint. Persist data, output, and logs
with writable volume mounts when results must survive container replacement.
The complete precedence and validation rules are in :doc:`containerization`.
