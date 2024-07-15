from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class paths:
    data_root = Path.home() / ".mapoc"
    colors = data_root / "colors.json"
    cities = data_root / "cities.csv"
    cities_hash = data_root / ".cities.hash"
    geofabrik_tree = data_root / "geofabrik_tree.json"
    geofabrik_tree_txt = data_root / "geofabrik_tree.txt"

