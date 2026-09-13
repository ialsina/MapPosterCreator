Installation
============

Requirements
------------

The packaging metadata declares Python 3.7 or newer, but the current source
uses annotation syntax that requires Python 3.10 or newer. Use Python 3.10+
and the packages listed in ``requirements.txt``. Its geospatial stack includes
GeoPandas, Shapely, and Fiona/GDAL; these packages may need system libraries
before pip can install them.

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
   pip install -r requirements.txt
   pip install -e .

The editable installation makes the ``mapoc`` command available. Verify it
with:

.. code-block:: bash

   mapoc --version
   mapoc --help

Build this documentation
------------------------

Install the documentation dependency alongside the application dependencies:

.. code-block:: bash

   pip install -r docs/requirements.txt
   sphinx-build -b html docs docs/_build/html

Open ``docs/_build/html/index.html`` in a browser. The default Alabaster theme
is intentionally used so documentation can build without an additional theme
package.
