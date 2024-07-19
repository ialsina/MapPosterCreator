from dataclasses import dataclass, field, asdict
from functools import lru_cache
import json
import logging
from typing import Mapping

from colour import Color
from matplotlib.colors import get_named_colors_mapping

from map_poster_creator.config import paths

logger = logging.getLogger(__name__)
_CONFIG_COLORSCHEME_PATH = paths.colors
_COLORSHCHEME_LIBRARY_FILES = (
    _CONFIG_COLORSCHEME_PATH,
    paths.dictionary_of_color_combinations,
)
_MATPLOTLIB_COLORS = get_named_colors_mapping()

@dataclass
class ColorScheme:
    facecolor: Color = field(default_factory=lambda: Color("#ffffff"))
    water: Color = field(default_factory=lambda: Color("#ffffff"))
    greens: Color = field(default_factory=lambda: Color("#ffffff"))
    roads: Color = field(default_factory=lambda: Color("#ffffff"))

    @staticmethod
    def _make_color(arg=None):
        _type_error = TypeError(
            f"Bad types in Color construction with argument {arg}."
        )
        if isinstance(arg, Color):
            return arg
        if arg is None:
            return Color("#000000")
        if isinstance(arg, str):
            if arg.startswith("#"):
                return Color(arg)
            return Color(_MATPLOTLIB_COLORS[arg])
        if isinstance(arg, (list, tuple)):
            if not all(isinstance(element, (int, float)) for element in arg):
                raise _type_error
            if not len(arg) == 3:
                raise _type_error
            return Color(rgb=arg)
        raise TypeError(
            f"Error while constructing Color, wrong type ()"
        )

    def __init__(self, facecolor, water=None, greens=None, roads=None):
        self.facecolor = self._make_color(facecolor)
        self.water = self._make_color(water or facecolor)
        self.greens = self._make_color(greens or facecolor)
        self.roads = self._make_color(roads or facecolor)

    def to_json(self):
        return {key: str(color.hex) for key, color in asdict(self).items()}


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Color):
            return o.hex
        elif isinstance(o, ColorScheme):
            return {"__ColorScheme__": o.to_json()}
        return super().default(o)

def object_hook(obj):
    if isinstance(obj, str):
        if obj.startswith("#"):
            return Color(obj)
    if isinstance(obj, dict):
        if "__ColorScheme__" in obj:
            return ColorScheme(**obj["__ColorScheme__"])
    return obj


_DEFAULT_SCHEMES = {
    "black": ColorScheme(
        (0, 0, 0),
        "#383d52",
        "#354038",
        "#ffffff",
    ),
    "white": ColorScheme(
        (1, 1, 1),
        "#bdddff",
        "#d4ffe1",
        "#000000",
    ),
    "red": ColorScheme(
        (0.4, 0.12, 0.12),
        "#754444",
        "#b36969",
        "#ffffff",
    ),
    "coral": ColorScheme(
        (0.67, 0.2, 0.18),
        "#ffffff",
        "#b36969",
        "#ffffff",
    ),
}

def _save_colorschemes(
    schemes: Mapping[str, ColorScheme],
) -> None:
    with open(_CONFIG_COLORSCHEME_PATH, "w") as cf:
        json.dump(schemes, cf, cls=JSONEncoder)
    logger.info(f"Save user colors config: {_CONFIG_COLORSCHEME_PATH}")

def _ensure_colorscheme_config_file() -> None:
    if _CONFIG_COLORSCHEME_PATH.is_file():
        return
    _CONFIG_COLORSCHEME_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"User colors config not found!")
    _save_colorschemes(schemes=_DEFAULT_SCHEMES)

@lru_cache(maxsize=None)
def get_colorschemes() -> dict[str, ColorScheme]:
    colorschemes = {}
    for file in _COLORSHCHEME_LIBRARY_FILES:
        with open(file, "r", encoding="utf-8") as cf:
            colorschemes.update(
                json.load(cf, object_hook=object_hook)
            )
    return colorschemes

@lru_cache(maxsize=None)
def get_available_colorschemes():
    return list(get_colorschemes().keys())

@lru_cache(maxsize=None)
def get_colorscheme(name):
    return get_colorschemes()[name]

def add_colorscheme(name: str, colorscheme: ColorScheme):
    colorschemes = get_colorschemes()
    colorschemes.update({name: colorscheme})
    _save_colorschemes(colorschemes)

def remove_colorscheme(name: str):
    colorschemes = get_colorschemes()
    del colorschemes[name]
    _save_colorschemes(colorschemes)

_ensure_colorscheme_config_file()

