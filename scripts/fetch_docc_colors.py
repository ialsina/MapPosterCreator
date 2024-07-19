from collections import defaultdict, UserList, UserDict
from dataclasses import dataclass, asdict
from functools import partial, lru_cache
from itertools import permutations
import json
from requests import Session
from requests.adapters import HTTPAdapter
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
    assignments = {
        "light": FunCollection(
            facecolor=colorops.lightest,
            roads=colorops.darkest,
            water=partial(colorops.closest, target="blue"),
            greens=partial(colorops.closest, target="green"),
        ),
        "dark": FunCollection(
            facecolor = colorops.lightest,
            roads = colorops.darkest,
            water = partial(colorops.closest, target="blue"),
            greens = partial(colorops.closest, target="green"),
        ),
    }

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
                colorschemes.update({
                    prefix + key + f"-{i}": csc
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

    for name, colors in docc_combinations.items():
        if len(colors) == 4:
            docc = DoccCombination(colors)
            prefix = f"~docc-{name}-"
            docc_schemes.update(
                docc.get_colorschemes(prefix)
            )

    return docc_schemes

if __name__ == "__main__":
    docc_schemes = get_docc_schemes()
    with open(FILE_PATH, "w", encoding="utf-8") as wf:
        json.dump(dict(docc_schemes), wf, cls=JSONEncoder)

