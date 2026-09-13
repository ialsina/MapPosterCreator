"""
Create geonames_headers.txt file required by fetch_data_geonames.py.

This file contains the column definitions for GeoNames cities1000.txt format.
Based on the standard GeoNames format documentation.
"""

import sys

from map_poster_creator.config import paths

# Standard GeoNames allCountries.txt / cities1000.txt column format
# See: https://download.geonames.org/export/dump/readme.txt
GEONAMES_HEADERS = """geonameid: integer id of record in geonames database
name: name of geographical point (utf8) varchar(200)
asciiname: name of geographical point in plain ascii characters, varchar(200)
alternatenames: alternatenames, comma separated varchar(5000)
latitude: latitude in decimal degrees (wgs84)
longitude: longitude in decimal degrees (wgs84)
feature class: see http://www.geonames.org/export/codes.html, char(1)
feature code: see http://www.geonames.org/export/codes.html, varchar(10)
country code: ISO-3166 2-letter country code, 2 characters
cc2: alternate country codes, comma separated, ISO-3166 2-letter country code, 60 characters
admin1 code: fipscode (subject to change to iso code), see exceptions below, varchar(20)
admin2 code: code for the second administrative division, a county in the US, see exceptions below, varchar(80)
admin3 code: code for third level administrative division, varchar(20)
admin4 code: code for fourth level administrative division, varchar(20)
population: bigint (8 byte int)
elevation: in meters, integer
dem: digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
timezone: the timezone id (see file timeZone.txt) varchar(40)
modification date: date of last modification in yyyy-MM-dd format
"""


def create_geonames_headers():
    """Create the geonames_headers.txt file if it doesn't exist."""
    headers_path = paths.geonames_headers

    if headers_path.exists():
        print(f"File {headers_path} already exists.")
        # Check for --yes flag for non-interactive mode
        auto_yes = "--yes" in sys.argv or "-y" in sys.argv
        if auto_yes:
            response = "y"
        else:
            response = input("Replace? [y/N] > ").lower()
        if response not in {"y", "yes", "true", "1"}:
            print("Skipping geonames_headers.txt creation.")
            return

    # Ensure directory exists
    headers_path.parent.mkdir(parents=True, exist_ok=True)

    # Write headers file
    with open(headers_path, "w", encoding="utf-8") as f:
        f.write(GEONAMES_HEADERS)

    print(f"Created {headers_path}")


if __name__ == "__main__":
    create_geonames_headers()
