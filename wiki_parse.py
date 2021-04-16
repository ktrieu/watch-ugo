from urllib.parse import urlparse
from dataclasses import dataclass
from typing import List

import wikitextparser as wtp
import requests

WIKIPEDIA_WIKITEXT_URL = "https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&formatversion=2&page="

session = requests.session()
session.headers.update({"User-Agent": "WatchUGO (kevin.trieu5813@gmail.com)"})


@dataclass
class VideoItem:
    # The name of the item
    name: str
    # The URL of the article that this item represents
    wikilink: str


def get_article_wikitext(article_title: str) -> str:
    request_url = WIKIPEDIA_WIKITEXT_URL + article_title
    response = session.get(request_url).json()
    return response["parse"]["wikitext"]


def parse_article_wikitext(article_url: str) -> wtp.WikiText:
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


def video_item_from_wikilink(wikilink: wtp.WikiLink) -> VideoItem:
    return VideoItem(wikilink.title, wikilink.target)


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
        video_items.extend(extract_section(s))

    return video_items