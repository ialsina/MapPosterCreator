from functools import lru_cache
import os
import subprocess
from pathlib import Path
import platform
from requests import Session
from requests.adapters import HTTPAdapter
from tempfile import NamedTemporaryFile
from typing import Optional
from urllib.parse import urljoin
import webbrowser
import wget
from zipfile import ZipFile

from bs4 import BeautifulSoup, Tag
from pandas import DataFrame, Series, read_csv
from map_poster_creator.config import paths
from unidecode import unidecode

GEOJSON_URL = "https://geojson.io/#map=10/{latitude}/{longitude}"
GEOFABRIK_URL = "https://download.geofabrik.de"

def is_valid_a_tag(a_tag: Tag) -> bool:
    return a_tag.attrs["href"].endswith("latest-free.shp.zip")

@lru_cache(maxsize=None)
def get_city_df() -> DataFrame:
    if not paths.cities_geonames_1000.exists():
        raise FileNotFoundError(
            "Could not find city data. Please download using the appropriate script."
        )
    return read_csv(
        paths.cities_geonames_1000,
        index_col=0,
        low_memory=False
    ).fillna("")

@lru_cache(maxsize=None)
def get_country_df() -> DataFrame:
    if not paths.countries.exists():
        raise FileNotFoundError(
            "Could not find country data. Please download using the appropriate script."
        )
    return read_csv(paths.countries)

def _interactive_resolve(df: DataFrame) -> Series:
    def row_txt(row):
        country_name = countries[
            countries["Code"] == row["country code"]
        ].iloc[0]["Name"]
        return f"{row['name']} ({country_name})"
    countries = get_country_df()
    choices = {i: row for i, (_, row) in enumerate(df.iterrows(), start=1)}
    print("\t" + "\n\t".join(f"{i}. {row_txt(row)}" for i, row in choices.items()))
    while True:
        user_input = input("\tSelect choice [1] >")
        if user_input == "":
            return choices[1]
        try:
            user_input = int(user_input)
            if user_input in choices:
                return choices[user_input]
        except ValueError:
            pass

@lru_cache
def resolve_city(
        city: str,
        country: Optional[str] = None,
        *,
        interactive: bool = True,
        element_if_one: bool = True,
        first: bool = False,
    ) -> DataFrame | Series | None:
    city_df = get_city_df()
    if country is None:
        candidates = city_df[
            city_df["asciiname"].apply(str.lower) == unidecode(city).lower()
        ].copy()
    else:
        countries = get_country_df()
        country_code = countries[
            countries["Name"].apply(str.lower) == country.lower()
        ].iloc[0]["Code"]
        candidates = city_df[
            (city_df["asciiname"].apply(str.lower) == unidecode(city).lower())
            & (city_df["country code"] == country_code)
        ].copy()
    candidates.sort_values(by="population", ascending=False, inplace=True)
    if candidates.shape[0] == 0:
        return None
    if candidates.shape[0] > 1 and interactive:
        return _interactive_resolve(candidates)
    if (candidates.shape[0] == 1 and element_if_one) or first:
        return candidates.iloc[0]
    return candidates

def _open_text_editor(file_path):
    """
    Opens a text editor with the specified file for the user to edit.
    Waits for the user to close the editor before continuing.
    """
    if platform.system() == 'Windows':
        subprocess.run(['notepad', file_path])
    elif platform.system() == 'Linux':
        subprocess.run(['nano', file_path])
    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(['open', '-a', 'TextEdit', file_path])
    else:
        raise SystemError(
            f"Unknown platform: {platform.system()}"
        )

def _remove_hash_trailing_lines(file):
    file.seek(0)
    edited_content = file.read().decode("utf-8").splitlines()
    filtered_content = [line for line in edited_content if not line.strip().startswith('#')]
    file.seek(0)
    file.truncate()
    file.write("".join(filtered_content).encode("utf-8"))

def browser_get_geojson_path_interactive(city: str, country: Optional[str] = None) -> Path:
    city_series = resolve_city(city, country)
    if city_series is None:
        raise ValueError(
            f'City "{city}" '
            + (f'and country "{country}" ' if country is not None else '')
            + "did not give any results."
        )
    webbrowser.open_new_tab(
        GEOJSON_URL.format(
            latitude=city_series["latitude"],
            longitude=city_series["longitude"])
    )
    with NamedTemporaryFile(mode="w+b", delete=False) as tf:
        filepath = tf.name
        tf.write(
            b"# Create the shape in the browser, and paste the JSON object below\n\n\n"
        )
        tf.flush()
        _open_text_editor(filepath)
        _remove_hash_trailing_lines(tf)
    return Path(filepath)


def _find_shp_url(region_url: str) -> str:
    with Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        response = session.get(region_url)
        if response.status_code != 200:
            raise IOError(
                f"Could not fetch resource (status code: {response.status_code}): "
                + str(region_url)
            )
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", recursive=True):
            if is_valid_a_tag(a_tag):
                return urljoin(region_url, a_tag.attrs["href"])
        raise ValueError(
            f"Couldn't find a satisfying a tag in {region_url}."
        )

def _get_extract_dir(path: Path, fname: str) -> Path:
    return (path / Path(fname).stem)

def _download_extract_shp(shp_url: str) -> Path:
    path = paths.shp_path
    path.mkdir(parents=True, exist_ok=True)
    fname = shp_url.split('/')[-1]
    if _get_extract_dir(path, fname).exists():
        return _get_extract_dir(path, fname)
    print(f"Downloading in: {path}")
    fname = wget.download(shp_url, out=str(path))
    zip_fpath = path / fname
    print(f"New zip file: {zip_fpath}")
    extract_dir = _get_extract_dir(path, fname)
    extract_dir.mkdir(parents=False, exist_ok=False)
    print(f"Extracting in: {extract_dir}")
    with ZipFile(zip_fpath, "r") as zf:
        zf.extractall(path=str(extract_dir))
    os.remove(zip_fpath)
    return extract_dir

def download_shp_interactive(city: str, country: Optional[str] = None) -> Path:
    webbrowser.open_new_tab(GEOFABRIK_URL)
    message = (
        "# Please, navigate to the page of the region corresponding to the city of "
        f"{city}{f', {country}' if country is not None else ''}.\n"
        "# Then, paste the URL below\n\n\n"
    )
    with NamedTemporaryFile(mode="w+b", delete=False) as tf:
        tf.write(message.encode("utf-8"))
        tf.flush()
        _open_text_editor(tf.name)
        _remove_hash_trailing_lines(tf)
        tf.seek(0)
        region_url = tf.read().decode("utf-8").strip()
        shp_url = _find_shp_url(region_url)
    extract_dir = _download_extract_shp(shp_url)
    return extract_dir

if __name__ == "__main__":
    download_shp_interactive("Barcelona")
