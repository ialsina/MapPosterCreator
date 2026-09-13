API reference
=============

This page covers the package's Python interfaces. The separately deployed
FastAPI interface is documented in :doc:`service`. This reference is kept
manually in sync with the source so documentation can build without importing
the native geospatial stack. Functions prefixed with an underscore are
implementation details and may change without compatibility guarantees.

Core rendering
--------------

``create_poster(shp_dir, geojson_path, color, width, dpi, output)``
  Loads the expected shapefile layers, clips them to a GeoJSON path or
  in-memory Polygon/MultiPolygon, and saves a PNG through the plotting layer.

``create_poster_from_coordinates(shp_dir, coordinates, color, width, dpi, output, geojson_output_path=None)``
  Constructs a polygon from longitude/latitude pairs and renders it. The
  polygon is passed in memory unless an intermediate GeoJSON output is
  requested.

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

``find_download_shp_from_point(point, calculate_point=False, interactive=False, location_name="point", interactive_callback=None)``
  Selects the smallest suitable Geofabrik region containing a Shapely point
  and downloads its shapefile archive.

``get_geojson_path_from_geoboundaries(city, country=None, country_code=None, interactive=False, interactive_callback=None)``
  Resolves a city, finds its administrative Polygon/MultiPolygon in local
  geoBoundaries data, and writes a GeoJSON boundary.

``get_city_df()``, ``get_country_df()``, ``get_regions_tree()``, ``get_geofabrik_urls()``, ``get_region_polygons()``, ``get_all_region_polygons()``, ``get_region_centroids()``, ``get_geoboundaries_gdf()``, and ``get_cities_geonames()``
  Cached loaders and derived indexes for generated local metadata.

Geometry and coordinate helpers
-------------------------------

``MapGeometry``
  Dataclass holding ``top``, ``bottom``, ``left``, ``right``, and ``center``
  map bounds.

``get_polygon_from_geojson(geojson_path)``
  Validates and loads the first Polygon or MultiPolygon Feature from a GeoJSON
  file. Interior rings are ignored.

``read_coordinates_from_file(file_path)``
  Reads a JSON array, CSV rows, or whitespace-separated longitude/latitude
  pairs.

``polygon_from_coordinates(coordinates)``
  Validates at least three coordinate pairs, closes the ring when necessary,
  and returns a Shapely Polygon.

``create_geojson_from_points(coordinates, output_path=None, name=None)``
  Builds a polygon and serializes it as a FeatureCollection.

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

``get_data_dir()`` and ``get_output_dir()``
  Resolve environment, YAML, and default locations and create the effective
  directories.

Logging
-------

``log_processing(func)``
  Decorator that logs a processing message before calling ``func``.

HTTP service types
------------------

``Coordinate``
  Pydantic longitude/latitude pair with geographic range validation.

``PosterRequest`` and ``PosterRequestSimple``
  Request models for object-based and array-based coordinate payloads,
  including optional shapefile/location hints and render settings.

``find_shp_from_latitude_longitude(latitude, longitude)``
  Selects a downloadable Geofabrik region from an explicit point.

``find_shp_from_polygon(polygon, city=None, country=None, latitude=None, longitude=None)``
  Selects a shapefile using explicit point coordinates, then city/country,
  then polygon centroid.

``register_endpoints(app)``
  Adds the root, health, colours, and two poster routes to a FastAPI
  application.
