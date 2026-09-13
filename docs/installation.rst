Installation
============

Requirements
------------

Use Python 3.10 or newer. Runtime dependencies are declared in
``pyproject.toml``. Its geospatial stack includes GeoPandas, Shapely, and
Fiona/GDAL; these packages may need system libraries before pip can install
them.

On Debian/Ubuntu systems, install GEOS development files first:

.. code-block:: bash

   sudo apt-get install libgeos-dev

On macOS, install GEOS with Homebrew:

.. code-block:: bash

   brew install geos

On Windows, use wheels compatible with your Python version for GDAL and Fiona
if pip cannot resolve their native dependencies. The original project README
links to prebuilt-wheel guidance.

Install from a checkout
-----------------------

From the repository root:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e .

The editable installation makes the ``mapoc`` command available. Verify it
with:

.. code-block:: bash

   mapoc --version
   mapoc --help

Prepare application data
------------------------

City lookup, automatic boundaries, and Geofabrik selection use generated
indexes that are not bundled with the source. The setup orchestrator creates
them in ``~/.mapoc`` by default:

.. code-block:: bash

   bash scripts/setup.sh

Full setup creates GeoNames headers, country and city indexes, a Geofabrik
region tree and URL map, geoBoundaries data, and optionally the extended
colour library. It performs large network downloads and may take several
minutes.

For coordinate-based operation without city lookup or automatic
geoBoundaries, use the smaller setup:

.. code-block:: bash

   bash scripts/setup.sh --tiny --non-interactive

Use ``--output DIR`` to select another data directory. It takes precedence
over ``MAPOC_DATA_DIR``. See :doc:`data-sources` for all modes and generated
files.

Run an application interface
----------------------------

Use :doc:`quickstart` for the command-line application. To expose the HTTP
interface, see :doc:`service`. A Docker image is also included, subject to
the current build limitation described in :doc:`containerization`.

Build this documentation
------------------------

Install the documentation dependency alongside the application dependencies:

.. code-block:: bash

   pip install -r docs/requirements.txt
   sphinx-build -b html docs docs/_build/html

Open ``docs/_build/html/index.html`` in a browser. The default Alabaster theme
is intentionally used so documentation can build without an additional theme
package.
