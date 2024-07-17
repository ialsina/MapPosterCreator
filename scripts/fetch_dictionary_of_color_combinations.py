from collections import defaultdict
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

with (
    Session() as session,
):
    session.mount("http://", HTTPAdapter(max_retries=3))
    session.mount("https://", HTTPAdapter(max_retries=3))
    response = session.get(DATA_URL, timeout=30)
    response.raise_for_status()
    colors_json = json.loads(response.text)

docc_colors = {}
docc_combinations = defaultdict(list)
docc_schemes = []

for color in colors_json:
    name = color["name"]
    hex = color["hex"]
    combinations = color["combinations"]
    docc_colors[name] = Color(hex)
    for combination in combinations:
        docc_combinations[combination].append(Color(hex))


with open(FILE_PATH, "w", encoding="utf-8") as wf:
    json.dump(dict(docc_combinations), wf, cls=JSONEncoder)

