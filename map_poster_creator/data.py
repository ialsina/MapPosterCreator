from functools import lru_cache
import platform
import subprocess
from pandas import DataFrame, Series, read_csv
from tempfile import NamedTemporaryFile
from typing import Optional
from unidecode import unidecode
import webbrowser

from map_poster_creator.config import paths

GEOJSON_URL = "https://geojson.io/#map=10/{latitude}/{longitude}"

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
    if first:
        return candidates.iloc[0]
    if candidates.shape[0] > 1 and interactive:
        return _interactive_resolve(candidates)
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

def browser_get_geojson_path_interactive(city: str, country: Optional[str] = None) -> str:
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
        return filepath

def find_shp(city: str, country: Optional[str] = None):
    raise NotImplementedError
