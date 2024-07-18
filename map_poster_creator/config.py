from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.yaml"
_DEFAULT_DATA_ROOT = Path.home() / ".mapoc"
_TEMP_DIR = Path(tempfile.gettempdir())


@dataclass(frozen=True)
class Config:
    data_root: Path = _DEFAULT_DATA_ROOT
    keep_shp_files: bool = False

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)


with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
    _config_dct = yaml.safe_load(cf) or {}

config = Config.from_dict(_config_dct)

@dataclass(frozen=True)
class paths:
    data_root = config.data_root
    colors = data_root / "colors.json"
    countries = data_root / "countries.csv"
    cities_gh_datasets = data_root / "cities_gh_datasets.csv"
    cities_gh_datasets_hash = data_root / ".cities_gh_datasets.hash"
    cities_geonames_1000 = data_root / "cities_geonames_1000.csv"
    cities_geonames_1000_txt = data_root / "cities_geonames_1000.txt"
    cities_geonames_1000_zip = data_root / "cities_geonames_1000.zip"
    dictionary_of_color_combinations = data_root / "docc_colors.json"
    geonames_headers = data_root / "geonames_headers.txt"
    geofabrik_tree_nw = data_root / "geofabrik_tree.nw"
    geofabrik_tree_txt = data_root / "geofabrik_tree.txt"
    geofabrik_urls = data_root / "geofabrik_urls.json"
    shp_path = (data_root if config.keep_shp_files else _TEMP_DIR) / "shp"

