import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin
from pprint import pprint
from unidecode import unidecode

from bs4 import BeautifulSoup
from ete3 import TreeNode

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

def find_tree(session, url, region="", depth=1) -> TreeNode:
    print(f"Navigating: {url:<100s}", end="\r")

    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return TreeNode()

    soup = BeautifulSoup(response.text, "html.parser")

    node = TreeNode(name=unidecode(region))
    node.add_feature("url", url)
    for table in find_tables(soup):
        pages = get_pages_from_table(table)
        for name, href in pages.items():
            if href.endswith(".html"):
                child_node = find_tree(
                    session=session,
                    url=urljoin(url, href),
                    region=name,
                    depth=depth+1,
                )
                if child_node:
                    node.add_child(child_node)
            else:
                leaf_node = TreeNode(name=unidecode(name))
                leaf_node.add_feature("url", urljoin(url, href))
                node.add_child(leaf_node)
    return node

def _tree_to_json(node):
    result = {"name": node.name}
    if node.is_leaf():
        result["url"] = node.url if "url" in node.features else ""
    else:
        result["children"] = [_tree_to_json(child) for child in node.get_children()]
    return result

if __name__ == "__main__":

    with requests.Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        root = find_tree(session, URL, "/")

    if root:
        root.write(format=1, features=["url"], outfile=paths.geofabrik_tree_nw)

        with open(paths.geofabrik_tree_txt, "w", encoding="utf-8") as wf:
            pprint(_tree_to_json(root), stream=wf)

