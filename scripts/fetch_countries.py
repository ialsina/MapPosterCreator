from ete3.coretype.seqgroup import write_fasta
import requests
from requests.adapters import HTTPAdapter
from map_poster_creator.config import paths

DATA_URL = "https://raw.githubusercontent.com/datasets/country-list/master/data.csv"

with (
    requests.Session() as session,
    open(paths.countries, "w", encoding="utf-8") as wf
):
    session.mount("http://", HTTPAdapter(max_retries=3))
    session.mount("https://", HTTPAdapter(max_retries=3))
    response = session.get(DATA_URL)
    if response.status_code == 200:
        wf.write(response.text)
    else:
        print(f"Couldn't fetch resource: {URL}.")


