from collections import defaultdict, UserList
import json
from requests import Session
from requests.adapters import HTTPAdapter

from map_poster_creator.config import paths
from map_poster_creator.colorscheme import Color, ColorScheme, JSONEncoder

DATA_URL = (
        "https://raw.githubusercontent.com/mattdesl/"
        "dictionary-of-colour-combinations/master/colors.json"
)
FILE_PATH = paths.dictionary_of_color_combinations

class DoccCombination(UserList):
    def __init__(self, lst):
        if len(lst) != 4:
            raise ValueError(
                f"We need 4 elements, there were {len(lst)}."
            )
        if not all(isinstance(element, Color) for element in lst):
            raise TypeError(
                f"We need all elements to be of type 'colours.Color'"
            )
        super().__init__(lst)

    @staticmethod
    def _distance(color1, color2):
        h1, s1, l1 = Color(color1).hsl
        h2, s2, l2 = Color(color2).hsl
        return (
            (h1 - h2) ** 2
            + (s1 - s2) ** 2
            + (l1 - l2) ** 2
        ) ** 0.5

    def _find_lightest(self, lst=None):
        lst = lst or self
        return min(lst, key=lambda x: x.luminance)

    def _find_darkest(self, lst=None):
        lst = lst or self
        return max(lst, key=lambda x: x.luminance)

    def _find_closest_to(self, target, lst=None):
        lst = lst or self
        return min(self, key=lambda x: self._distance(x, target))

    def get_colorschemes(self, prefix: str):
        lst = list(self)
        greens = self._find_closest_to("green")
        water = self._find_closest_to("blue")
        if greens == water:
            return {}
        lst.remove(greens)
        lst.remove(water)
        return {
            prefix + "light": ColorScheme(
                facecolor=self._find_lightest(lst),
                roads=self._find_darkest(lst),
                water=water,
                greens=greens,
            ),
            prefix + "dark": ColorScheme(
                facecolor=self._find_darkest(lst),
                roads=self._find_lightest(lst),
                water=water,
                greens=greens,
            )
        }

with (
    Session() as session,
):
    session.mount("http://", HTTPAdapter(max_retries=3))
    session.mount("https://", HTTPAdapter(max_retries=3))
    response = session.get(DATA_URL, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    colors_json = json.loads(response.text)

docc_colors = {}
docc_combinations = defaultdict(list)
docc_schemes = {}

for color in colors_json:
    name = color["name"]
    hex = color["hex"]
    combinations = color["combinations"]
    docc_colors[name] = Color(hex)
    for combination in combinations:
        docc_combinations[combination].append(Color(hex))

for name, colors in docc_combinations.items():
    if len(colors) == 4:
        docc = DoccCombination(colors)
        prefix = f"docc-{name}-"
        docc_schemes.update(
            docc.get_colorschemes(prefix)
        )

with open(FILE_PATH, "w", encoding="utf-8") as wf:
    json.dump(dict(docc_schemes), wf, cls=JSONEncoder)

