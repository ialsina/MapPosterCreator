import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time


URL_BASE = "http://download.geofabrik.de"


def crawl(
    url,
    follow_exts,
    extract_exts,
    max_depth=2,
    visited=None,
    results=None,
    domain_limit=None,
):
    """
    Recursively crawls hyperlinks from a URL.

    Args:
        url (str): starting URL
        follow_exts (list): list of extensions to follow recursively
        extract_exts (list): list of extensions to include in final results
        max_depth (int): max recursion depth
        visited (set): set of visited URLs
        results (list): final results list
        domain_limit (str): limit crawl to this domain

    Returns:
        None (results are appended to the results list)
    """
    if visited is None:
        visited = set()
    if results is None:
        results = []

    if max_depth < 0 or url in visited:
        return

    visited.add(url)
    print(f"Crawling: {url}")

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    for a in soup.find_all("a", href=True):
        absolute_url = urljoin(url, a["href"])
        parsed_url = urlparse(absolute_url)

        # Ignore non-http(s) links
        if parsed_url.scheme not in ("http", "https"):
            continue

        # Optional domain limit
        if domain_limit and parsed_url.netloc != domain_limit:
            continue

        path_lower = parsed_url.path.lower()

        # Decide whether to follow
        follow = any(path_lower.endswith(ext) for ext in follow_exts)

        # Decide whether to extract
        extract = not extract_exts or any(
            path_lower.endswith(ext) for ext in extract_exts
        )

        if extract:
            print(f"URL: {absolute_url}")
            results.append(absolute_url)

        # Recursively follow links
        if follow and absolute_url not in visited:
            crawl(
                absolute_url,
                follow_exts,
                extract_exts,
                max_depth - 1,
                visited,
                results,
                domain_limit,
            )
            time.sleep(0.3)  # polite delay


def main():
    parser = argparse.ArgumentParser(description="Recursive hyperlink crawler")
    parser.add_argument(
        "--follow",
        nargs="+",
        default=[".html", ".htm"],
        help="File extensions to follow recursively (default: .html .htm)",
    )
    parser.add_argument(
        "--extract",
        nargs="+",
        default=None,
        help="File extensions to include in final results (default: all)",
    )

    args = parser.parse_args()

    domain_limit = urlparse(URL_BASE).netloc
    results = []

    crawl(
        URL_BASE,
        args.follow,
        args.extract,
        max_depth=3,
        domain_limit=domain_limit,
        results=results,
    )

    print("\nFinal extracted links:")
    for link in sorted(set(results)):
        print(link)


if __name__ == "__main__":
    main()
