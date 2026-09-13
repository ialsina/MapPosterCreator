Command-line interface
======================

``mapoc`` is the installed console command. Run ``mapoc --help`` or append
``--help`` to any command for argparse-generated help.

Poster creation
---------------

.. code-block:: text

   mapoc poster [CITY] [--shp-path SHP_PATH] [--geojson-path GEOJSON_PATH]
                [--coordinates-file COORDINATES_FILE]
                [--country-code COUNTRY_CODE] [--interactive]
                [--colors NAME [NAME ...]] [--width WIDTH] [--dpi DPI]
                [--output-prefix PREFIX]

``CITY`` may be ``City`` or ``City, Country``. It is required when the command
must obtain a boundary or shapefile directory automatically, but may be
omitted when both inputs are explicit. Ambiguous matches select the
highest-population city unless ``--interactive`` is set.

Options:

* ``--shp-path`` — an extracted Geofabrik shapefile directory.
* ``--geojson-path`` — a Polygon or MultiPolygon FeatureCollection.
* ``--coordinates-file`` — a polygon as a JSON array, CSV rows, or
  whitespace-separated rows of ``longitude latitude``. It cannot be combined
  with ``--geojson-path``.
* ``-c``, ``--country-code`` — a two-letter code used to narrow city lookup.
* ``-i``, ``--interactive`` — prompt for city or region selection when
  multiple candidates exist. Automatic selection is the default.
* ``--colors`` — one or more colour-scheme names. Defaults to ``white``.
  Unknown names are skipped with a message.
* ``-w``, ``--width`` — square poster width. An unqualified number and values
  ending in ``cm`` are interpreted as centimetres; ``in`` means inches.
  Default: ``15cm``.
* ``-d``, ``--dpi`` — output resolution in dots per inch. Default: ``300``.
* ``--output-prefix`` — filename prefix. One ``<prefix>_<scheme>.png`` is
  produced per requested scheme. Without a city or explicit prefix,
  ``polygon_poster`` is used.

When a city is supplied without ``--geojson-path``, its boundary is selected
from the locally generated geoBoundaries data. If automatic shapefile
selection fails, the CLI falls back to the interactive Geofabrik workflow.
See :doc:`data-sources` for the full and tiny data sets.

Pixel widths (``px``) are recognised by the argument parser but are not
implemented and raise ``NotImplementedError``. Any other suffix raises
``ValueError``.

Browser shortcuts
-----------------

.. code-block:: text

   mapoc browse shp
   mapoc browse geojson

``browse shp`` opens Geofabrik in a new browser tab; ``browse geojson`` opens
geojson.io. These commands only open websites—they do not download data or
write boundary files.

Colour commands
---------------

.. code-block:: text

   mapoc color list
   mapoc color show NAME
   mapoc color add NAME --facecolor COLOR --water COLOR --greens COLOR --roads COLOR

``list`` prints registered schemes and their component colours. ``show``
displays a Matplotlib palette window. ``add`` saves or replaces a named scheme
in the user's colour configuration. Each colour accepts a hexadecimal string
or a Matplotlib named colour. Details are in :doc:`color-schemes`.

Exit behavior and errors
------------------------

If no service is selected, the relevant help text is printed. Invalid GeoJSON,
unknown cities, unavailable metadata, download failures, and incompatible
geometries surface as Python exceptions. For expected inputs and sources, see
:doc:`quickstart`, :doc:`data-sources`, and :doc:`troubleshooting`.

The HTTP interface is separate from the ``mapoc`` command and is documented
in :doc:`service`.
