Development
===========

Repository layout
-----------------

``map_poster_creator/``
  Application package and ``mapoc`` console entry point.

``scripts/``
  One-off or maintenance scripts that build required local indexes and
  generated palette data.

``config.yaml``
  Repository-root configuration loaded by ``map_poster_creator.config``.

``requirements.txt`` and ``setup.py``
  Runtime dependency list and package metadata/console-script declaration.

``docs/``
  This Sphinx documentation source.

Set up a development environment
--------------------------------

Follow :doc:`installation`, then install the package in editable mode:

.. code-block:: bash

   pip install -e .
   pip install -r docs/requirements.txt

The repository currently has no automated test suite or formatter
configuration. Verify a focused change by exercising the affected command or
function with representative local data, then build the documentation:

.. code-block:: bash

   sphinx-build -W -b html docs docs/_build/html

``-W`` treats documentation warnings as errors and is appropriate for CI or
pre-merge verification.

Working with external data
--------------------------

Do not commit generated GeoNames, Geofabrik, shapefile, or colour-library
data unless the project specifically adopts a distribution policy for it.
These datasets can be large and are sourced from external projects. Use
:doc:`data-sources` to reproduce them locally.

The maintenance scripts run as plain Python scripts and assume configured
paths are available. They perform HTTP requests and, in several cases, write
files into ``data_dir``. Review source URLs and generated paths before running
them in automated environments.

Compatibility notes
-------------------

``setup.py`` declares ``python_requires='>=3.7'``, but the current source
contains PEP 604 union annotations (for example ``str | None``), whose syntax
requires Python 3.10 or newer. Use Python 3.10+ unless the code and package
metadata are aligned as part of a separate compatibility change.
