from itertools import islice, takewhile, repeat
from typing import List, Dict, Callable, Union
import random
import html

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
        action="parse",
        page=html.unescape(article_title),
        prop="wikitext",
        formatversion="2",
        redirects=True,
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


def commons_search_image(search: str) -> Union[str, None]:
    """
    Search Wikimedia Commons for `search`, and returns the *name*
    of the first image result. Returns None if no image was found.
    """
    # Wikimedia Commons lets us specify a MIME type to filter by images only
    search_query = search + " filetype:image"
    response = commons_session.get(
        action="query", list="search", srsearch=search_query, srnamespace="6"
    )

    if len(response["query"]["search"]) == 0:
        return None

    first_result = response["query"]["search"][0]

    return first_result["title"]


def get_fallback_article_image_url(article_title: str) -> Union[str, None]:
    """
    Some Wikipedia articles have no associated image. As a fallback, we search on
    Wikimedia Commons with the article title and grab the first result.
    Returns None if no fallback image could be found.
    """
    cleaned_article_title = (
        article_title.replace("_", " ").replace("(", "").replace(")", "")
    )
    fallback_image_title = commons_search_image(cleaned_article_title)

    if fallback_image_title is None:
        return None

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


# This is an overestimate to avoid skipping pages
N_LIST_OF_ARTICLES = 300000


def get_random_list_article(progress_lambda: Callable[[int], None] = None) -> str:
    """
    Get a random "List of" article title.

    Since this is a long-running operation, a progress_lambda can be passed in that will be called
    before every request with the number of articles seen.
    """

    article_idx = random.randint(0, N_LIST_OF_ARTICLES)
    print(f"Selected random article number {article_idx}.")

    n_articles_seen = 0
    r = wikipedia_session.get(
        action="query", list="allpages", aplimit=500, apprefix="List of"
    )
    while True:
        for p in r["query"]["allpages"]:
            if n_articles_seen == article_idx:
                return p["title"]
            n_articles_seen += 1
        if r.get("continue", None) is None:
            # we've reached the end, just return the last one
            return r["query"]["allpages"][-1]["title"]
        else:
            if progress_lambda:
                progress_lambda(n_articles_seen)
            r = wikipedia_session.get(
                action="query",
                list="allpages",
                aplimit=500,
                apprefix="List of",
                apcontinue=r["continue"]["apcontinue"],
            )


def get_url_from_article_title(title):
    r = wikipedia_session.get(action="query", prop="info", inprop="url", titles=title)

    normalized = r["query"].get("normalized", None)
    if normalized:
        return get_url_from_article_title(normalized["to"])

    # get first and only page in the page dictionary
    page = list(r["query"]["pages"].items())[0][1]
    url = page.get("fullurl", None)
    if url is not None:
        return url
    else:
        raise RuntimeError(f"Page {title} not found.")
