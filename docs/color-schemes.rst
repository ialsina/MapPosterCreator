Colour schemes
==============

A colour scheme has four roles:

``facecolor``
  Figure background.
``water``
  Water-area fill.
``greens``
  Point-of-interest-area fill.
``roads``
  Road line colour.

Built-in schemes
----------------

The initial user colour file contains ``black``, ``white``, ``red``, and
``coral``. Use ``mapoc color list`` to inspect the exact values currently
available; the result may also contain generated or previously saved schemes.

Create or replace a scheme
--------------------------

.. code-block:: bash

   mapoc color add coffee \
     --facecolor "#433633" \
     --water "#5c5552" \
     --greens "#8f857d" \
     --roads "#decbb7"

Colours may be hexadecimal RGB values or Matplotlib named colours, such as
``navy``. Adding a name that already exists updates the in-memory mapping and
writes the merged mapping to ``<data_dir>/colors.json``.

Use palettes
------------

Render one poster for each named scheme:

.. code-block:: bash

   mapoc poster "Berlin, Germany" --colors white coffee coral

Preview a palette interactively:

.. code-block:: bash

   mapoc color show coffee

``show`` opens a Matplotlib window and therefore needs a graphical plotting
backend.

Storage precedence and caveat
-----------------------------

``get_colorschemes`` loads both the user ``colors.json`` and generated
``docc_colors.json``. Later loaded entries replace earlier entries with the
same name. The generated Dictionary of Colour Combinations file is expected to
exist when the colour module loads; use the generator in :doc:`data-sources`
to create it if it is missing.

The command-line ``add`` operation writes the complete currently loaded map to
the user file. It does not clear the in-process cache, so changes made outside
the current process are not observed until the next run.
