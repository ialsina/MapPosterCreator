"""Utility functions for data operations.

This module contains utility functions for file operations, URL handling,
downloads, and formatting that are used across the data package.
"""

import os
import platform
import subprocess
from pathlib import Path
from urllib.parse import urljoin
from zipfile import ZipFile

import wget
from bs4 import BeautifulSoup, Tag
from pandas import Series
from requests import Session
from requests.adapters import HTTPAdapter

from map_poster_creator.config import GEOFABRIK_HREF_ATTRIBUTE_END, paths


# URL validation functions
def is_valid_download_url(url: str, href_end: str = None) -> bool:
    """Check if URL is a valid GeoFabrik download URL."""
    if href_end is None:
        href_end = GEOFABRIK_HREF_ATTRIBUTE_END
    return url.endswith(href_end)


def is_valid_a_tag(a_tag: Tag, href_end: str = None) -> bool:
    """Check if an HTML tag is a valid download link."""
    if href_end is None:
        href_end = GEOFABRIK_HREF_ATTRIBUTE_END
    return is_valid_download_url(a_tag.attrs["href"], href_end)


# File editing utilities
def _open_text_editor(file_path):
    """
    Opens a text editor with the specified file for the user to edit.
    Waits for the user to close the editor before continuing.
    """
    if platform.system() == "Windows":
        subprocess.run(["notepad", file_path], check=False)
    elif platform.system() == "Linux":
        subprocess.run(["nano", file_path], check=False)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", "-a", "TextEdit", file_path], check=False)
    else:
        raise SystemError(f"Unknown platform: {platform.system()}")


def _remove_hash_trailing_lines(file):
    """Remove lines starting with '#' from a file."""
    file.seek(0)
    edited_content = file.read().decode("utf-8").splitlines()
    filtered_content = [
        line for line in edited_content if not line.strip().startswith("#")
    ]
    file.seek(0)
    file.truncate()
    file.write("".join(filtered_content).encode("utf-8"))


def _ask_reuse(city):
    """Ask user if they want to reuse an existing GeoJSON file."""
    print(f"Geojson file found for {city}.")
    return input("Reuse? [Y/n] >").lower() not in {"n", "no", "false", "0"}


def _exit_if_empty_file(file):
    """Exit if the file is empty."""
    file.seek(0)
    if not file.read():
        raise SystemExit


# URL and download utilities
def _get_extract_dir(path: Path, fname: str) -> Path:
    """Get the extraction directory path for a zip file."""
    return path / Path(fname).stem


def _find_shp_url(region_url: str, href_end: str = None) -> str:
    """Find the SHP download URL from a GeoFabrik region page."""
    if href_end is None:
        href_end = GEOFABRIK_HREF_ATTRIBUTE_END
    with Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        response = session.get(region_url)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            raise OSError(
                f"Could not fetch resource (status code: {response.status_code}): "
                + str(region_url)
            )
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", recursive=True):
            if is_valid_a_tag(a_tag, href_end):
                return urljoin(region_url, a_tag.attrs["href"])
        raise ValueError(f"Couldn't find a satisfying a tag in {region_url}.")


def _download_extract_shp(shp_url: str) -> Path:
    """Download and extract a SHP zip file."""
    path = paths.shp_path
    path.mkdir(parents=True, exist_ok=True)
    fname = shp_url.split("/")[-1]
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


# Formatting utilities
def format_city_candidate(row: Series) -> str:
    """
    Format a city candidate row for display.

    Args:
        row: A pandas Series representing a city candidate

    Returns:
        Formatted string like "City Name, Admin1, Admin2, ..., Country"
    """
    from map_poster_creator.data.getters import get_country_df

    countries = get_country_df()
    country_name = countries[countries["Code"] == row["country code"]].iloc[0]["Name"]
    admin_lst = [row[f"admin{i} code"] for i in range(4, 0, -1)]
    admin_lst.append(country_name)
    admin_txt = ", ".join(el for el in admin_lst if el)
    return f"{row['name']}, {admin_txt}"
