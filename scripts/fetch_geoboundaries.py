"""
Download geoBoundariesCGAZ_ADM2.geojson file.

This file contains administrative boundaries for cities and regions.
Downloaded from the geoBoundaries project.
"""

import sys
import requests
from requests.adapters import HTTPAdapter
from map_poster_creator.config import paths

# geoBoundaries CGAZ ADM2 download URL
# This is the Comprehensive Global Administrative Zones (CGAZ) dataset
# ADM2 refers to second-level administrative divisions (cities, counties, etc.)
GEOBOUNDARIES_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/"
    "release-data/gbOpen/CGAZ/ADM2/geoBoundariesCGAZ_ADM2.geojson"
)


def fetch_geoboundaries():
    """Download geoBoundariesCGAZ_ADM2.geojson file."""
    output_path = paths.geoboundaries_path

    if output_path.exists():
        print(f"File {output_path} already exists.")
        # Check for --yes flag for non-interactive mode
        auto_yes = "--yes" in sys.argv or "-y" in sys.argv
        if auto_yes:
            response = "y"
        else:
            response = input("Replace? [y/N] > ").lower()
        if response not in {"y", "yes", "true", "1"}:
            print("Skipping geoboundaries download.")
            return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading geoBoundaries from {GEOBOUNDARIES_URL}...")
    print("This may take several minutes due to the large file size...")

    try:
        with requests.Session() as session:
            session.mount("http://", HTTPAdapter(max_retries=3))
            session.mount("https://", HTTPAdapter(max_retries=3))

            response = session.get(GEOBOUNDARIES_URL, timeout=300, stream=True)
            response.raise_for_status()

            # Get file size for progress indication
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}%", end="", flush=True)

            print(f"\nDownloaded {output_path}")
            print(f"File size: {downloaded / (1024 * 1024):.2f} MB")

    except requests.RequestException as e:
        print(f"Error downloading geoboundaries: {e}")
        if output_path.exists():
            output_path.unlink()
        raise


if __name__ == "__main__":
    fetch_geoboundaries()
