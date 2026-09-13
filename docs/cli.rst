Command-line interface
======================

``mapoc`` is the installed console command. Run ``mapoc --help`` or append
``--help`` to any command for argparse-generated help.

Poster creation
---------------

.. code-block:: text

   mapoc poster [CITY] [--shp-path SHP_PATH] [--geojson-path GEOJSON_PATH]
                [--colors NAME [NAME ...]] [--width WIDTH] [--dpi DPI]
                [--output-prefix PREFIX]

``CITY`` is required by the current argument parser and may be ``City`` or
``City, Country``. The country improves ambiguous city resolution. If it is
omitted, matches are sorted by population and you are prompted only if there
are multiple candidates. Supplying both explicit input paths avoids resolving
the supplied city, but does not make the positional argument optional.

Options:

* ``--shp-path`` — an extracted Geofabrik shapefile directory.
* ``--geojson-path`` — a polygon boundary file.
* ``--colors`` — one or more colour-scheme names. Defaults to ``white``.
  Unknown names are skipped with a message.
* ``--width`` — square poster width. An unqualified number and values ending
  in ``cm`` are interpreted as centimetres; ``in`` means inches. Default:
  ``15cm``.
* ``--dpi`` — output resolution in dots per inch. Default: ``300``.
* ``--output-prefix`` — filename prefix. One ``<prefix>_<scheme>.png`` is
  produced per requested scheme.

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
