from dataclasses import dataclass
from pathlib import Path
import os
import tempfile
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.yaml"
# Check for environment variable first (for containerization), then use default
_DEFAULT_DATA_DIR = Path(os.getenv("MAPOC_DATA_DIR", str(Path.home() / ".mapoc")))
_DEFAULT_OUTPUT_DIR = Path(os.getenv("MAPOC_OUTPUT_DIR", str(Path.home() / "mapoc")))
_TEMP_DIR = Path(tempfile.gettempdir())

# Ensure data_dir and output_dir exist
if _DEFAULT_DATA_DIR:
    _DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
if _DEFAULT_OUTPUT_DIR:
    _DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
        # Convert string paths to Path objects
        processed = {}
        for key, value in dct.items():
            if key in ('data_dir', 'output_dir'):
                processed[key] = Path(value) if isinstance(value, str) else value
            else:
                processed[key] = value
        return cls(**processed)


def get_data_dir() -> Path:
    """Get data directory from environment variable, config file, or default.
    Creates the directory if it doesn't exist."""
    # Check environment variable first (highest priority)
    env_data_dir = os.environ.get("MAPOC_DATA_DIR")
    if env_data_dir:
        data_dir = Path(env_data_dir).expanduser().resolve()
    else:
        # Then check config file
        with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
            _config_dct = yaml.safe_load(cf) or {}

        if "data_dir" in _config_dct:
            data_dir = Path(_config_dct["data_dir"]).expanduser().resolve()
        else:
            # Default fallback
            data_dir = _DEFAULT_DATA_DIR

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_output_dir() -> Path:
    """Get output directory from environment variable, config file, or default.
    Creates the directory if it doesn't exist."""
    # Check environment variable first (highest priority)
    env_output_dir = os.environ.get("MAPOC_OUTPUT_DIR")
    if env_output_dir:
        output_dir = Path(env_output_dir).expanduser().resolve()
    else:
        # Then check config file
        with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
            _config_dct = yaml.safe_load(cf) or {}

        if "output_dir" in _config_dct:
            output_dir = Path(_config_dct["output_dir"]).expanduser().resolve()
        else:
            # Default fallback
            output_dir = _DEFAULT_OUTPUT_DIR

    # Create directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# Load config with environment variable support
with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
    _config_dct = yaml.safe_load(cf) or {}

# Environment variables take highest precedence over config file
# Use get_data_dir() and get_output_dir() to ensure directories are created
if "MAPOC_DATA_DIR" in os.environ:
    _config_dct["data_dir"] = str(get_data_dir())
if "MAPOC_OUTPUT_DIR" in os.environ:
    _config_dct["output_dir"] = str(get_output_dir())

config = Config.from_dict(_config_dct)

# Compute actual data and output directories (respecting environment variables)
_actual_data_dir = get_data_dir()
_actual_output_dir = get_output_dir()


@dataclass(frozen=True)
class paths:
    data_dir = _actual_data_dir
    output_dir = _actual_output_dir
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
    geoboundaries_path = data_dir / "geoBoundariesCGAZ_ADM2.geojson"
    shp_path = (data_dir if config.keep_shp_files else _TEMP_DIR / "mapoc") / "shp"
    geojson_path = (
        data_dir if config.keep_geojson_files else _TEMP_DIR / "mapoc"
    ) / "geojson"


# URL constants
GEOJSON_URL = "https://geojson.io/#map=10/{latitude}/{longitude}"
GEOFABRIK_URL = "https://download.geofabrik.de"
GEOFABRIK_HREF_ATTRIBUTE_END = "latest-free.shp.zip"
