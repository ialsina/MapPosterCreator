import json
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin
from pprint import pprint

from bs4 import BeautifulSoup

from map_poster_creator.config import paths

URL = "https://download.geofabrik.de/"

def find_tables(soup):
    subregions = soup.find_all("table", id="subregions", recursive=True)
    special_subregions = soup.find_all("table", id="specialsubregions", recursive=True)
    return subregions + special_subregions

def get_pages_from_table(table):
    pages = {}
    for row in table.find_all("tr", recursive=True):
        td = row.find_all("td")
        if not td:
            continue
        for a_tag in td[0].find_all("a"):
            pages[a_tag.text] = a_tag.attrs.get("href")
    return pages

def find_tree(session, url, region="", depth=1):
    print(f"Navigating: {url}")

    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return dict(tree)

    soup = BeautifulSoup(response.text, "html.parser")

    nodes = []
    for table in find_tables(soup):
        pages = get_pages_from_table(table)
        for name, href in pages.items():
            if href.endswith(".html"):
                nodes.append(
                    find_tree(session,
                              urljoin(url, href),
                              name,
                              depth=depth+1,
                              )
                )
            else:
                nodes.append(urljoin(url, href))
    return {region: nodes}

with requests.Session() as session:
    session.mount("http://", HTTPAdapter(max_retries=3))
    session.mount("https://", HTTPAdapter(max_retries=3))
    tree = find_tree(session, URL)

with open(paths.geofabrik_tree, "w", encoding="utf-8") as wf:
    json.dump(tree, wf)

with open(paths.geofabrik_tree.stem + ".txt", encoding="utf-8") as wf:
    pprint(tree, stream=wf)



