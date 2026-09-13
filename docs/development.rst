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

``pyproject.toml``
  Package metadata, runtime dependencies, and console-script declaration.

``docs/``
  This Sphinx documentation source.

Set up a development environment
--------------------------------

Follow :doc:`installation`, then install the package in editable mode:

.. code-block:: bash

   pip install -e .
   pip install -r docs/requirements.txt

Install development tooling and enable the git hooks:

.. code-block:: bash

   pip install -e ".[dev]"
   pre-commit install

Pre-commit runs Ruff linting/formatting and basic file hygiene checks on each
commit. The repository currently has no automated test suite. Verify a focused
change by exercising the affected command or function with representative local
data, then build the documentation:

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

``pyproject.toml`` declares ``requires-python = ">=3.10"``, matching the PEP 604
union annotations used in the source (for example ``str | None``).
