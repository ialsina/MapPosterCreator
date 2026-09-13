"""Sphinx configuration for Map Poster Creator."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from map_poster_creator import __author__, __version__

project = "Map Poster Creator"
author = __author__
release = __version__
copyright = f"2020, {author}"

extensions = [
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"

html_theme = "alabaster"
html_static_path = ["_static"]
html_title = f"{project} {release}"

autodoc_member_order = "bysource"
autodoc_typehints = "description"
