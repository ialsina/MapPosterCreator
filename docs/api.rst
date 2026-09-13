API reference
=============

The command-line interface is the supported user interface. This reference is
kept manually in sync with the source so it can build without importing the
application's optional native geospatial stack. Functions prefixed with an
underscore are implementation details and may change without compatibility
guarantees.

Core rendering
--------------

``create_poster(shp_dir, geojson_path, color, width, dpi, output)``
  Loads the expected shapefile layers, clips them to a GeoJSON polygon, and
  saves a PNG through the plotting layer.

``shp_filename``
  Dataclass-like container for the fixed road, water, and green shapefile
  basenames.

CLI entry points
----------------

``map_poster(argv=None)``
  Parses command-line arguments and dispatches the selected service.

``get_parser()``
  Returns the root ``ArgumentParser`` and service-specific help callbacks.

Data acquisition and lookup
---------------------------

``resolve_city(city, country=None, interactive=True, element_if_one=True, first=False)``
  Searches local GeoNames city data, optionally prompts for an ambiguous
  match, and returns a Pandas row, table, or ``None``.

``browser_get_geojson_path_interactive(city, country=None)``
  Opens geojson.io and a local text editor to create or reuse a boundary file.

``download_shp_interactive(city, country=None)``
  Opens Geofabrik, requests a region page URL through a local editor, then
  downloads and extracts the matching archive.

``find_download_shp(city, country=None, calculate_point=False, interactive=False)``
  Selects a cached Geofabrik region for a resolved city and downloads its
  shapefile archive.

``get_city_df()``, ``get_country_df()``, ``get_regions_tree()``, and ``get_geofabrik_urls()``
  Cached loaders for generated local metadata.

GeoJSON helpers
---------------

``MapGeometry``
  Dataclass holding ``top``, ``bottom``, ``left``, ``right``, and ``center``
  map bounds.

``get_polygon_from_geojson(geojson_path)``
  Validates and loads the first Polygon Feature from a GeoJSON file.

``get_map_geometry_from_poly(poly)``
  Converts Shapely polygon bounds into ``MapGeometry``.

Plotting
--------

``road_width(speed)``
  Maps a speed band to a Matplotlib line width.

``plot_dataframe(ax, gdf, **kwargs)``
  Draws a GeoPandas dataframe on an axis.

``plot_and_save(roads, water, greens, cscheme, geometry, path, dpi=300, width=None, figsize=(8, 8))``
  Composes the layers, applies map bounds, and saves the figure.

Colour schemes
--------------

``ColorScheme(facecolor, water=None, greens=None, roads=None)``
  Holds four ``colour.Color`` values. Inputs can be hexadecimal strings,
  Matplotlib named colours, RGB triples, or ``Color`` objects.

``get_colorschemes()``, ``get_available_colorschemes()``, and ``get_colorscheme(name)``
  Access the cached palette library.

``add_colorscheme(name, colorscheme)`` and ``remove_colorscheme(name)``
  Persist palette changes in the user colour file.

``JSONEncoder`` and ``object_hook``
  Serialize and deserialize colour values and schemes.

Configuration
-------------

``Config``
  Frozen dataclass for data/output locations and default render settings.

``config``
  Configuration instance loaded from root ``config.yaml``.

``paths``
  Namespace of derived data, cache, and output paths.

Logging
-------

``log_processing(func)``
  Decorator that logs a processing message before calling ``func``.
