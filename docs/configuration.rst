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

The current ``Config.from_dict`` passes YAML values through without converting
strings to ``pathlib.Path`` objects, while the ``paths`` class uses the ``/``
operator. Consequently, a YAML ``data_dir`` or ``output_dir`` string can fail
at import time. Leave those values unset to use the working defaults, or align
the implementation's path coercion before relying on path overrides.

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
