from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class paths:
    data_root = Path.home() / ".mapoc"
    colors = data_root / "colors.json"
    cities_gh_datasets = data_root / "cities_gh_datasets.csv"
    cities_gh_datasets_hash = data_root / ".cities_gh_datasets.hash"
    cities_geonames_1000_txt = data_root / "cities_geonames_1000.txt"
    cities_geonames_1000_zip = data_root / "cities_geonames_1000.zip"
    geonames_headers = data_root / "geonames_headers.txt"
    geofabrik_tree_nw = data_root / "geofabrik_tree.nw"
    geofabrik_tree_txt = data_root / "geofabrik_tree.txt"

