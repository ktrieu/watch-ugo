from itertools import islice, takewhile, repeat
from typing import List, Dict

import mwapi


USER_AGENT = "WatchUGO/1.0 (kevin.trieu5813@gmail.com)"

wikipedia_session = mwapi.Session("https://en.wikipedia.org", user_agent=USER_AGENT)

commons_session = mwapi.Session("https://commons.wikimedia.org/", user_agent=USER_AGENT)


def split_every(n, iterable):
    """
    Slice an iterable into chunks of n elements
    :type n: int
    :type iterable: Iterable
    :rtype: Iterator
    """
    iterator = iter(iterable)
    return takewhile(bool, (list(islice(iterator, n)) for _ in repeat(None)))


def get_article_wikitext(article_title: str) -> str:
    response = wikipedia_session.get(
        action="parse", page=article_title, prop="wikitext", formatversion="2"
    )
    return response["parse"]["wikitext"]


def get_article_image_url(article_title: str) -> str:
    response = wikipedia_session.get(
        action="query",
        titles=article_title,
        prop="pageimages",
        piprop="original",
        pilicense="any",
        redirects=True,
    )
    pages = response["query"]["pages"]
    # Wikipedia returns a dictionary of pages.
    # Since we only ever query one, we can just grab the first one.
    page = list(pages.items())[0][1]
    if "original" in page:
        return page["original"]["source"]
    else:
        return None


def commons_search_image(search: str) -> str:
    """
    Search Wikimedia Commons for `search`, and returns the *name*
    of the first image result.
    """
    # Wikimedia Commons lets us specify a MIME type to filter by images only
    search_query = search + " filetype:image"
    response = commons_session.get(
        action="query", list="search", srsearch=search_query, srnamespace="6"
    )

    first_result = response["query"]["search"][0]

    return first_result["title"]


def get_fallback_article_image_url(article_title: str) -> str:
    """
    Some Wikipedia articles have no associated image. As a fallback, we search on
    Wikimedia Commons with the article title and grab the first result.
    """
    fallback_image_title = commons_search_image(article_title)

    response = commons_session.get(
        action="query", prop="imageinfo", titles=fallback_image_title, iiprop="url"
    )
    pages = response["query"]["pages"]
    # Wikipedia returns a dictionary of pages.
    # Since we only ever query one, we can just grab the first one.
    page = list(pages.items())[0][1]

    return page["imageinfo"][0]["url"]


EXTRACTS_MAX_CHARS = 500


def get_article_extract(article_title: str) -> str:
    response = wikipedia_session.get(
        action="query",
        prop="extracts",
        exchars=EXTRACTS_MAX_CHARS,
        explaintext=True,
        exintro=True,
        titles=article_title,
        redirects=True,
    )
    pages = response["query"]["pages"]
    # Wikipedia returns a dictionary of pages.
    # Since we only ever query one, we can just grab the first one.
    page = list(pages.items())[0][1]
    return page["extract"]


MAX_TITLES_PER_QUERY = 50


def get_articles_exists(article_titles: List[str]) -> Dict[str, bool]:
    """
    Determine whether the list of given article titles exists.
    Returns a dictionary of booleans, keyed by article titles.

    Because we will be doing this for *every* link on a page,
    this query works in bulk.
    """
    result = {}

    title_chunks = split_every(MAX_TITLES_PER_QUERY, article_titles)

    for chunk in title_chunks:
        joined_titles = "|".join(chunk)
        responses = wikipedia_session.get(
            action="query", prop="info", titles=joined_titles, continuation=True
        )

        for r in responses:
            # Wikipedia auto-normalizes any pages we give it. To return the same titles
            # we were called with, we have to reverse that.
            denormalize = {}
            for entry in r["query"]["normalized"]:
                denormalize[entry["to"]] = entry["from"]

            for _, page in r["query"]["pages"].items():
                exists = "missing" not in page
                denormalized_title = denormalize.get(page["title"], page["title"])
                result[denormalized_title] = exists

    return result