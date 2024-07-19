"""
Fetch colors of A Dictionary of Color Combinations Vol 1, by Sanzo Wada,
from the repository maintained by Matt DesLauriers (github.com/mattdesl).

At first, the idea was to loop for all the combinations, and choose those
with greener tones for ColorScheme.greens, bluer tones for ColorScheme.water,
Then, a light version could be provided by assigning the lighter and darker 
tones to ColorScheme.facecolor and ColorScheme.roads, respectively.
Finally, a darker version was provided with the opposite.

The issue, however lied in that, depending on how colors where chosen from the
color combination, this would lead to an arbitrarily chosen ColorScheme created
from the palette. For example, color combination #334 offers two equally valid
light-themed combinations, either by assigning the darker or lighter green to
ColorScheme.greens and the other one to ColorScheme.roads, or vice versa.

For this reason, a slightly more complex approach is taken in the current script.
Here, we create all possible algorithms for color choosing, based on permutations
of the color-picking sequence. Thus, if the color combination is

    { #1, #2, #3, #4 }

a possible ColorScheme could result from a particular color-picking sequence, say,

    lightest (#1) -> darkest (#4) -> greenest (#2) -> bluest (#3)

while aanother one would result from a different color-picking sequence, say,

    greenest (#1) -> lightest (#2) -> bluest (#4) -> darkest (#3).

Between parentheses is the picked color from among the remaining unpicked ones.
This example would arise from a color combination in which color #1 is lighter
than #2 but greener than #1, and color #4 is darker than #3, but also bluer.
In this particular example, by assigning "lightest" to ColorScheme.facecolor,
"darkest" to ColorScheme.roads, "bluest" to ColorScheme.water, and "greenest"
to ColorScheme.greens, we would have created two light-themed ColorSchemes. By
exchanging "lightest" and "darkest", we would have created two dark-themed ones.

Hence, by assigning a value to each of the possible color-picking sequences, then
discarding all the sequences that yield identical ColorSchemes, we have a collection
of light-themed and dark-themed ColorSchemes for each color combination of the book.
The typical number of unique ColorSchemes arising for each combination is 3 to 5 for
light and likewise for dark themes. The convention than we follow for naming the
combinations is:

    ~docc-XXX-theme-Y

Where docc stands for "A Dictionary of Color Combinations", XXX is the combination
number in the book, theme is either "light" or "dark", and "-Y", as a suffix, is an
identifier for  each of the possible combination outcomes. In case there is a single
one, the whole suffix (including the hyphen) is omitted. The tilde ("~") is so that
the names of the combinations sort last in an alphabetical list.
"""

from collections import defaultdict, UserList, UserDict
from dataclasses import dataclass, asdict
from functools import partial, lru_cache
from itertools import permutations
import json
from requests import Session
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from typing import Sequence, Any, Callable, List, Optional

from map_poster_creator.config import paths
from map_poster_creator.colorscheme import Color, ColorScheme, JSONEncoder

DATA_URL = (
        "https://raw.githubusercontent.com/mattdesl/"
        "dictionary-of-colour-combinations/master/colors.json"
)
FILE_PATH = paths.dictionary_of_color_combinations

class colorops:
    @staticmethod
    def distance(x1: Any, x2: Any) -> float:
        h1, s1, l1 = Color(x1).hsl
        h2, s2, l2 = Color(x2).hsl
        return (
            (h1 - h2) ** 2
            + (s1 - s2) ** 2
            + (l1 - l2) ** 2
        ) ** 0.5

    @staticmethod
    def closest(lst: Sequence[Any], target: Any) -> Any:
        distance = colorops.distance
        return min(lst, key=lambda x: distance(x, target))

    @staticmethod
    def lightest(lst: Sequence[Any]) -> Any:
        return max(lst, key=lambda x: Color(x).luminance)

    @staticmethod
    def darkest(lst: Sequence[Any]) -> Any:
        return min(lst, key=lambda x: Color(x).luminance)

@dataclass
class FunCollection:
    pass

@dataclass
class Fun2Collection(FunCollection):
    facecolor: Callable
    roads: Callable

@dataclass
class Fun3Collection(FunCollection):
    facecolor: Callable
    roads: Callable
    greens: Callable

@dataclass
class Fun4Collection(FunCollection):
    facecolor: Callable
    roads: Callable
    water: Callable
    greens: Callable

class AlgoFactory:
    def __init__(self, collection: FunCollection, verbose: bool = False):
        self._collection = asdict(collection)
        self._iterator = self._generate_permutations()
        self.verbose = verbose

    @staticmethod
    def _wrapper(keys, funs, verbose):
        def algorithm(lst: List):
            lst = lst.copy()
            filtered = {}
            for key, fun in zip(keys, funs):
                if verbose:
                    print(f"\t\tApplying {fun.__name__} -> {key}")
                element = fun(lst)
                lst.remove(element)
                filtered[key] = element
            return filtered
        return algorithm

    def _generate_permutations(self):
        collection = self._collection
        for permutation in permutations(collection.items()):
            keys, funs = list(zip(*permutation))
            yield self._wrapper(keys, funs, self.verbose)

    def __iter__(self):
        self._iterator = self._generate_permutations()
        return self

    def __next__(self):
        try:
            return next(self._iterator)
        except StopIteration:
            raise StopIteration

class DoccCombination(UserList):
    _assignments = {
        2: {
            "light": Fun2Collection(
                facecolor=colorops.lightest,
                roads=colorops.darkest,
            ),
            "dark": Fun2Collection(
                facecolor = colorops.darkest,
                roads = colorops.lightest,
            ),
        },
        3: {
            "light": Fun3Collection(
                facecolor=colorops.lightest,
                roads=colorops.darkest,
                greens=partial(colorops.closest, target="green"),
            ),
            "dark": Fun3Collection(
                facecolor = colorops.darkest,
                roads = colorops.lightest,
                greens = partial(colorops.closest, target="green"),
            ),
        },
        4: {
            "light": Fun4Collection(
                facecolor=colorops.lightest,
                roads=colorops.darkest,
                water=partial(colorops.closest, target="blue"),
                greens=partial(colorops.closest, target="green"),
            ),
            "dark": Fun4Collection(
                facecolor = colorops.lightest,
                roads = colorops.darkest,
                water = partial(colorops.closest, target="blue"),
                greens = partial(colorops.closest, target="green"),
            ),
        },
    }

    def __init__(self, lst):
        if len(lst) not in {2, 3, 4}:
            raise ValueError(
                f"We need 2, 3 or 4 elements. There were {len(lst)}."
            )
        if not all(isinstance(element, Color) for element in lst):
            raise TypeError(
                f"We need all elements to be of type 'colours.Color'"
            )
        self.assignments = self._assignments[len(lst)]
        super().__init__(lst)

    def _get_colorschemes(self, key, unique=True):
        lst = list(self).copy()
        assignment = self.assignments[key]
        colorschemes = []
        for algorithm in AlgoFactory(assignment):
            colors = algorithm(lst)
            colorscheme = ColorScheme(**colors)
            colorschemes.append(colorscheme)
        if not unique:
            return colorschemes
        return list(set(colorschemes))


    def get_colorschemes(self, prefix: str, unique: bool = True):
        colorschemes = {}
        for key in self.assignments.keys():
            key_colorschemes = self._get_colorschemes(key, unique=unique)
            for i, csc in enumerate(key_colorschemes, start=1):
                suffix = (
                    f"-{i:d}"
                    if len(key_colorschemes) > 1
                    else ""
                )
                colorschemes.update({
                    prefix + key + suffix: csc
                })
        return colorschemes

@lru_cache(maxsize=None)
def get_docc_combinations():
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

    for color in colors_json:
        name = color["name"]
        hex = color["hex"]
        combinations = color["combinations"]
        docc_colors[name] = Color(hex)
        for combination in combinations:
            docc_combinations[combination].append(Color(hex))

    return dict(docc_combinations)


def get_docc_schemes():
    docc_combinations = get_docc_combinations()
    docc_schemes = {}

    with tqdm(total=len(docc_combinations), leave=False) as pbar:
        for name, colors in docc_combinations.items():
            docc = DoccCombination(colors)
            prefix = f"~docc-{name:03d}-"
            docc_schemes.update(
                docc.get_colorschemes(prefix)
            )
            pbar.update()

    return docc_schemes

if __name__ == "__main__":
    docc_schemes = get_docc_schemes()
    with open(FILE_PATH, "w", encoding="utf-8") as wf:
        json.dump(dict(docc_schemes), wf, cls=JSONEncoder)

