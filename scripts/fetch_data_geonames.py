from pandas import read_csv
import wget
from zipfile import ZipFile
import shutil
import os

from map_poster_creator.config import paths

DATA_URL = "https://download.geonames.org/export/dump/cities1000.zip"

def ask_replace(file):
    print(f"File {file} already exists.")
    return input("Replace? [y/N] >").lower() in {"y", "yes", "true", "1"}

def fetch_data():
    paths.cities_geonames_1000_zip.parent.mkdir(parents=True, exist_ok=True)
    wget.download(DATA_URL, out=str(paths.cities_geonames_1000_zip))
    fpath = paths.cities_geonames_1000_txt
    with ZipFile(paths.cities_geonames_1000_zip, "r") as zf:
        namelist = zf.namelist()
        for name in namelist:
            if os.path.isfile(fpath.parent / name):
                os.remove(fpath.parent / name)
        zf.extractall(fpath.parent)


    if len(namelist) == 1:
        shutil.move(
            fpath.parent / namelist[0],
            fpath
        )
        return None
    for i, name in enumerate(namelist, start=1):
        shutil.move(
            fpath.parent / name,
            fpath.parent / f"{fpath.stem}_{i:03s}{fpath.suffix}"
        )
    return None

def get_header():
    columns = []
    with open(paths.geonames_headers, "r", encoding="utf-8") as hf:
        for line in hf:
            if line.strip().startswith("#"):
                continue
            columns.append(
                line.strip().split(":")[0].strip()
            )
    return columns

def read_cities_df():
    return read_csv(
        paths.cities_geonames_1000_txt,
        sep="\t",
        names=get_header(),
        low_memory=False
    )

def clean_data():
    os.remove(paths.cities_geonames_1000_txt)
    os.remove(paths.cities_geonames_1000_zip)


if __name__ == "__main__":
    if paths.cities_geonames_1000_zip.exists():
        if ask_replace(paths.cities_geonames_1000_zip):
            os.remove(paths.cities_geonames_1000_zip)
            fetch_data()
    else:
        fetch_data()
    cities_df = read_cities_df()
    cities_df.to_csv(paths.cities_geonames_1000, index=True)
    clean_data()

