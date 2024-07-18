from collections import defaultdict
import json
from requests import Session, RequestException
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin
from pprint import pprint
from unidecode import unidecode
from tqdm import tqdm
from typing import Tuple, Mapping, Sequence

from bs4 import BeautifulSoup
from ete3 import TreeNode

from map_poster_creator.config import paths

URL = "https://download.geofabrik.de/"
UrlsType = Mapping[str, Sequence[str]]
print = tqdm.write

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

def _get_description(url: str, region: str) -> str:
    max_url = 60
    max_region = 30
    url = (
        url
        if len(url) <= max_url
        else url[:(max_url - 3)] + "..."
    )
    region = (
        region
        if len(region) <= max_region
        else region[:(max_region - 3)] + "..."
    )
    return f"{region:>{max_region}s}: {url:<{max_url}s}"

def find_tree(session) -> Tuple[TreeNode, UrlsType]:
    def navigate_node(url, region="", depth=1):
        print(_get_description(url, region), end="\r")

        response = session.get(url)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            print(f"Request failed: {url}", end="\r")
            return TreeNode()

        soup = BeautifulSoup(response.text, "html.parser")

        node = TreeNode(name=unidecode(region))
        node.add_feature("url", url)
        for table in find_tables(soup):
            pages = get_pages_from_table(table)
            for name, href in pages.items():
                if href.endswith(".html"):
                    child_node = navigate_node(
                        url=urljoin(url, href),
                        region=unidecode(name),
                        depth=depth+1,
                    )
                    if child_node:
                        node.add_child(child_node)
                else:
                  region_urls[region].append(urljoin(url, href))
        return node

    print(f"Building tree. Navigating site {URL}...\n")
    region_urls = defaultdict(list)
    region_tree = navigate_node(URL)
    return region_tree, dict(region_urls)

def fetch_polygons(
        session: Session,
        tree: TreeNode,
        urls: UrlsType,
    ) -> None:
    print("Fetching polygons:")
    tree_iter = tree.traverse()
    if tree_iter is None:
        return
    with tqdm(total=len(tree), leave=True) as pbar:
        for node in tree_iter:
            node_name = unidecode(node.name)
            pbar.set_description(node_name)
            print(f"{node_name:<90s}", end="\r")
            try:
                poly_url = next(
                    filter(lambda x: x.endswith(".poly"), urls[node_name])
                )
                response = session.get(poly_url)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                node.add_feature("polygon", response.text)
            except (StopIteration, KeyError, RequestException):
                print(f"Couldn't fetch polygon for {node_name}")
            pbar.update()

def _tree_to_json(node):
    result = {"name": node.name}
    if node.is_leaf():
        result["url"] = node.url if "url" in node.features else ""
    else:
        result["children"] = [_tree_to_json(child) for child in node.get_children()]
    return result

if __name__ == "__main__":

    with Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        tree, urls = find_tree(session)
        fetch_polygons(session, tree, urls)

    if tree is not None:
        tree.write(format=1, features=["url", "polygon"], outfile=paths.geofabrik_tree_nw)

        with open(paths.geofabrik_tree_txt, "w", encoding="utf-8") as wf:
            pprint(_tree_to_json(tree), stream=wf)

    with open(paths.geofabrik_urls, "w", encoding="utf-8") as wf:
        json.dump(urls, wf)

