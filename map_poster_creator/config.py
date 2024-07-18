from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.yaml"
_DEFAULT_DATA_DIR = Path.home() / ".mapoc"
_DEFAULT_OUTPUT_DIR = Path.home() / "mapoc"
_TEMP_DIR = Path(tempfile.gettempdir())


@dataclass(frozen=True)
class Config:
    data_dir: Path = _DEFAULT_DATA_DIR
    output_dir: Path = _DEFAULT_OUTPUT_DIR
    default_width: str = "15cm"
    default_dpi: int = 300
    keep_shp_files: bool = False
    keep_geojson_files: bool = False

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)


with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
    _config_dct = yaml.safe_load(cf) or {}

config = Config.from_dict(_config_dct)

@dataclass(frozen=True)
class paths:
    data_dir = config.data_dir
    output_dir = config.output_dir
    colors = data_dir / "colors.json"
    countries = data_dir / "countries.csv"
    cities_gh_datasets = data_dir / "cities_gh_datasets.csv"
    cities_gh_datasets_hash = data_dir / ".cities_gh_datasets.hash"
    cities_geonames_1000 = data_dir / "cities_geonames_1000.csv"
    cities_geonames_1000_txt = data_dir / "cities_geonames_1000.txt"
    cities_geonames_1000_zip = data_dir / "cities_geonames_1000.zip"
    dictionary_of_color_combinations = data_dir / "docc_colors.json"
    geonames_headers = data_dir / "geonames_headers.txt"
    geofabrik_tree_nw = data_dir / "geofabrik_tree.nw"
    geofabrik_tree_txt = data_dir / "geofabrik_tree.txt"
    geofabrik_urls = data_dir / "geofabrik_urls.json"
    shp_path = (data_dir if config.keep_shp_files else _TEMP_DIR / "mapoc") / "shp"
    geojson_path = (data_dir if config.keep_geojson_files else _TEMP_DIR / "mapoc") /"geojson"

