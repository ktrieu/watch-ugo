from urllib.parse import urlparse
from dataclasses import dataclass
from typing import List, Dict
from itertools import islice, takewhile, repeat

import vid_def
import wikitextparser as wtp
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
            # we were called it, we have to reverse that.
            denormalize = {}
            for entry in r["query"]["normalized"]:
                denormalize[entry["to"]] = entry["from"]

            for _, page in r["query"]["pages"].items():
                exists = "missing" not in page
                denormalized_title = denormalize.get(page["title"], page["title"])
                result[denormalized_title] = exists

    return result


def get_article_title_from_url(url: str) -> str:
    """
    Extracts the Wikipedia article title from a Wikipedia URL.

    This returns the URL in unescaped form, i.e., Like_This.
    """
    # url parse doesn't properly parse the domain if a protocol isn't present
    if not url.startswith("http"):
        url = "http://" + url

    result = urlparse(url)
    if result.netloc != "en.wikipedia.org" or not result.path.startswith("/wiki/"):
        raise ValueError(
            "The article URL must have the format en.wikipedia.org/wiki/<title>."
        )

    return result.path.replace("/wiki/", "")


def parse_article_wikitext(article_url: str) -> wtp.WikiText:
    """
    Requests and parses the list article at article_url.
    The URL must be in the format en.wikipedia.org/wiki/<title>
    or an error will be raised.
    """

    article_title = get_article_title_from_url(article_url)
    wikitext = get_article_wikitext(article_title)
    parsed = wtp.parse(wikitext)
    return parsed


def escape_wikilink_target(target: str) -> str:
    """
    Escape bare wikilink article titles so we can pass them into the API.
    This is almost certainly broken.
    """
    return target.replace(" ", "_")


@dataclass
class VideoItem:
    # The name of the item
    name: str
    # The title of the article that this item represents
    article_title: str


def video_item_from_wikilink(wikilink: wtp.WikiLink) -> VideoItem:
    return VideoItem(wikilink.title, escape_wikilink_target(wikilink.target))


def extract_list(wikilist: wtp.WikiList) -> List[VideoItem]:
    """
    Extracts ListItems from a WikiList. We use some heuristics:
    - the FIRST Wikilink in a list item is the main article it refers to
    - if a list contains no Wikilinks, it doesn't contain any data we're interested in
      so we return an empty list.
    """
    video_items = []
    for item in wikilist.items:
        # items are returned as string for some reason, so we have to reparse
        wikilinks = wtp.parse(item).wikilinks
        if len(wikilinks) > 0:
            video_items.append(video_item_from_wikilink(wikilinks[0]))

    return video_items


def extract_section(section: wtp.Section) -> List[VideoItem]:
    video_items = []
    # according to docs, this weird pattern will flatten lists
    for l in section.get_lists("\*+"):
        video_items.extend(extract_list(l))

    return video_items


def extract_video_items(parsed: wtp.WikiText) -> List[VideoItem]:
    video_items = []

    for s in parsed.get_sections(include_subsections=True):
        # skip the See Also section, which can contain lists
        if s.title == "See also":
            continue
        video_items.extend(extract_section(s))

    return video_items


MAX_CHARS = 500


def clean_extract(extract: str) -> str:
    """
    Do some cleaning work on an article extract from the Wikipedia API.

    We remove any partial sentences that might be at the end of the extract,
    as well as remove any newlines, and unescape apostrophes.
    """

    # poor man's sentence boundary detection
    try:
        last_period = extract.rindex(". ")
        extract = extract[: last_period + 1]
    except ValueError:
        # no leftover sentence, whatever
        pass

    extract = extract.replace("\n", "")
    extract = extract.replace(r"\'", r"'")

    return extract


def segment_from_video_item(item: VideoItem) -> "vid_def.Segment":
    """
    Builds a segment from the given video item.
    """
    segment_desc = clean_extract(get_article_extract(item.article_title))

    image_url = get_article_image_url(item.article_title)
    if image_url is None:
        image_url = get_fallback_article_image_url(item.article_title)

    return vid_def.Segment(
        name=item.name, description=segment_desc, image_url=image_url
    )
