import requests
from requests.exceptions import RequestException
from pandas import read_csv
import wget

from map_poster_creator.config import paths

API_URL = "https://api.github.com/repos/datasets/world-cities/commits?path=data/world-cities.csv"
DATA_URL = "https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv"

def get_github_commit_hash():
    if not paths.cities_hash.exists():
        return ""
    with open(paths.cities_hash, "r", encoding="utf-8") as hf:
        return hf.read()

def get_saved_commit_hash():
    response = requests.get(API_URL, timeout=20)
    commits = response.json()
    return commits[0]['sha']

def fetch_data():
    paths.cities.parent.mkdir(parents=True, exist_ok=True)
    wget.download(DATA_URL, out=str(paths.cities))
    with open(paths.cities_hash, "w", encoding="utf-8") as hf:
        hf.write(get_github_commit_hash())

def read_cities_df():
    return read_csv(paths.cities)


if __name__ == "__main__":
    try:
        if get_github_commit_hash() != get_saved_commit_hash():
            fetch_data()
        cities_df = read_cities_df()
    except RequestException as exc:
        try:
            cities_df = read_cities_df()
        except FileNotFoundError:
            raise IOError(
                f"Cities info does not exist, couldn't fetch it due to an error"
            ) from exc

