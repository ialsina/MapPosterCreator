from pathlib import Path
from typing import Optional
import webbrowser
from tempfile import NamedTemporaryFile
from pandas import DataFrame, Series
from ete3 import Tree

from map_poster_creator.config import paths
from map_poster_creator.data import (
    resolve_city,
    _open_text_editor,
    _remove_hash_trailing_lines,
    _ask_reuse,
    _exit_if_empty_file,
    _find_shp_url,
    _download_extract_shp,
    GEOJSON_URL,
    GEOFABRIK_URL,
)
from map_poster_creator.data.models import _country_df

def get_country_df():
    """Get country DataFrame from the model."""
    return _country_df.data

def interactive_resolve_city(df: DataFrame) -> Series:
    def row_txt(row):
        country_name = countries[
            countries["Code"] == row["country code"]
        ].iloc[0]["Name"]
        admin_lst = [row[f"admin{i} code"] for i in range(4, 0, -1)]
        admin_lst.append(country_name)
        admin_txt = ", ".join(el for el in admin_lst if el)
        return f"{row['name']}, {admin_txt}"
    countries = get_country_df()
    choices = {i: row for i, (_, row) in enumerate(df.iterrows(), start=1)}
    print("Choose city:")
    print("\t" + "\n\t".join(
        f"{i}. {row_txt(row)}" for i, row in choices.items()
    ))
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


def browser_get_geojson_path_interactive(city: str, country: Optional[str] = None) -> Path:
    path = paths.geojson_path
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{city}.geojson"
    if filepath.exists():
        if _ask_reuse(city):
            return filepath
    city_series = resolve_city(city=city, country=country)
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
    with open(filepath, "w+b") as tf:
        filepath = tf.name
        tf.write(
            b"# Create the shape in the browser, and paste the JSON object below\n\n\n"
        )
        tf.flush()
        _open_text_editor(filepath)
        _remove_hash_trailing_lines(tf)
        _exit_if_empty_file(tf)
    return Path(filepath)


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



def interactive_region_choose(sorted_distances, num_choices=5) -> Tree:
    top_regions = list(zip(*sorted_distances))[0][:num_choices]
    choices = {i: region for i, region in enumerate(top_regions, start=1)}
    print("Choose region:")
    print("\t" + "\n\t".join(
        f"{i}. {node.name}" for i, node in choices.items())
    )
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
