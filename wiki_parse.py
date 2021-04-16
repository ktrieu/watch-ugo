from urllib.parse import urlparse
import wikitextparser as wtp

import requests

WIKIPEDIA_WIKITEXT_URL = "https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&formatversion=2&page="

session = requests.session()
session.headers.update({"User-Agent": "WatchUGO (kevin.trieu5813@gmail.com)"})


def get_article_wikitext(article_title: str):
    request_url = WIKIPEDIA_WIKITEXT_URL + article_title
    response = session.get(request_url).json()
    print(response)
    return response["parse"]["wikitext"]


def parse_article_wikitext(article_url: str):
    """
    Requests and parses the list article at article_url.
    The URL must be in the format en.wikipedia.org/wiki/<title>
    or an error will be raised.
    """

    # url parse doesn't properly parse the domain if a protocol isn't present
    if not article_url.startswith("http"):
        article_url = "http://" + article_url

    result = urlparse(article_url)
    if result.netloc != "en.wikipedia.org" or not result.path.startswith("/wiki/"):
        raise ValueError(
            "The article URL must have the format en.wikipedia.org/wiki/<title>."
        )

    article_title = result.path.replace("/wiki/", "")
    wikitext = get_article_wikitext(article_title)
    parsed = wtp.parse(wikitext)
    return parsed
