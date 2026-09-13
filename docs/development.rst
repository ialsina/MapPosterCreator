Development
===========

Repository layout
-----------------

``src/map_poster_creator/``
  Application package, ``mapoc`` entry point, data layer, geometry helpers,
  and FastAPI service.

``assets/``
  README and documentation images.

``scripts/``
  One-off or maintenance scripts that build required local indexes and
  generated palette data.

``config.yaml``
  Repository-root configuration loaded by ``map_poster_creator.config``.

``pyproject.toml``
  Package metadata, runtime dependencies, and console-script declaration.

``docs/``
  This Sphinx documentation source.

``tests/``
  Pytest unit/integration tests, curl-based service tests, fixtures, and
  example requests.

``examples/``
  Coordinate-based poster and rendering-debug examples.

``Dockerfile`` and ``docker-entrypoint.sh``
  HTTP service image and runtime data preparation.

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
commit. Run all configured hooks with:

.. code-block:: bash

   pre-commit run --all-files

Testing
-------

``pytest.ini`` discovers tests under ``tests/``, enables branch coverage for
``map_poster_creator``, writes terminal, HTML, and XML reports, and enforces a
70 percent coverage threshold:

.. code-block:: bash

   pytest

Run focused suites when iterating:

.. code-block:: bash

   pytest tests/test_core.py
   pytest tests/test_data_core.py
   pytest tests/test_api_endpoints.py
   pytest tests/test_api_utils.py
   pytest tests/test_poster_integration.py

Most unit tests mock network and large data dependencies. Integration and
poster-generation tests may require prepared data or shapefiles.

The shell suites exercise a running service:

.. code-block:: bash

   uvicorn map_poster_creator.api:app --host 0.0.0.0 --port 8000
   ./tests/test_api.sh --port 8000
   ./tests/test_posters.sh --port 8000

``API_BASE_URL``, ``VERBOSE``, and ``OUTPUT_DIR`` configure the curl-based
tests. ``tests/run_all_tests.sh`` is an interactive wrapper around them.

Documentation verification
--------------------------

Build the documentation with warnings treated as errors:

.. code-block:: bash

   sphinx-build -W -b html docs docs/_build/html

``-W`` treats documentation warnings as errors and is appropriate for CI or
pre-merge verification. These checks are available for local pipelines, but
the repository currently has no committed CI/CD workflow.

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

The Docker build also invokes ``scripts/setup.sh`` when prepared data is not
available. It currently references a missing root ``requirements.txt`` and
cannot complete from an unmodified checkout; see :doc:`containerization`.

Compatibility notes
-------------------

``pyproject.toml`` declares ``requires-python = ">=3.10"``, matching the PEP 604
union annotations used in the source (for example ``str | None``).
