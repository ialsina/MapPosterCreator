Troubleshooting
===============

City commands fail before rendering
-----------------------------------

City-driven poster creation requires generated files under ``data_dir``,
including country data, GeoNames city data, and the Geofabrik region tree.
Follow :doc:`data-sources`. Be aware that the GeoNames script also requires
``geonames_headers.txt``, which is not included in this checkout. Until that
file and the generated indexes are available, provide both ``--shp-path`` and
``--geojson-path`` (while retaining the required positional city argument).

Colour commands fail with a missing file
----------------------------------------

The colour loader reads both ``colors.json`` and ``docc_colors.json``. The
former is created automatically on first colour-module import, but the latter
is not bundled. Run ``python scripts/fetch_docc_colors.py`` to generate it, or
make the generated colour library available at the configured data path.

GeoJSON is rejected
-------------------

Use a FeatureCollection with at least one Feature whose geometry type is
``Polygon``. Do not supply a MultiPolygon. Only the first Feature and the
first polygon ring are used, so place the desired exterior boundary first.

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

The present configuration loader does not coerce YAML path strings to
``pathlib.Path`` before deriving child paths. Leave ``data_dir`` and
``output_dir`` unset to use defaults, or update that implementation before
using YAML path overrides. See :doc:`configuration`.
