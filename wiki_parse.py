from urllib.parse import urlparse
from dataclasses import dataclass
from typing import List, Tuple, Union

import vid_def
import wiki_api
import wikitextparser as wtp


def get_article_title_from_url(url: str) -> str:
    """
    Extracts the Wikipedia article title from a Wikipedia URL.

    This returns the URL in unescaped form, i.e., Like_This.

    If the URL is not in the format en.wikipedia.org/wiki/<title>,
    a ValueError is raised.
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


def parse_article_wikitext(article_title: str) -> wtp.WikiText:
    """
    Requests and parses the Wikipedia article named article_title.
    """
    wikitext = wiki_api.get_article_wikitext(article_title)
    parsed = wtp.parse(wikitext)
    return parsed


def escape_article_title(title: str) -> str:
    """
    Escape bare wikilink article titles so we can pass them into the API.
    This is almost certainly broken.
    """
    return title.replace(" ", "_")


def unescape_article_title(title: str) -> str:
    """
    Unescape article titles for display.
    As the inverse of above, this is also probably broken.
    """

    return title.replace("_", " ")


@dataclass
class VideoItem:
    # The name of the item
    name: str
    # The title of the article that this item represents
    article_title: str


def video_item_from_wikilink(wikilink: wtp.WikiLink) -> VideoItem:
    return VideoItem(wikilink.title, escape_article_title(wikilink.target))


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


# If a column has more than ACCEPTABLE_UNIQUE_FRACTION unique items, it's eligible
ACCEPTABLE_UNIQUE_FRACTION = 0.9
# Some columns have very few links, but as long as there are a few, the column should be eligible
ACCEPTABLE_LINK_FRACTION = 0.1


def parse_column(
    table: wtp.Table, column_idx: int, n_rows: int
) -> Tuple[List[wtp.WikiLink], bool]:
    """
    Parse a column of a WikiText table. For performance, we return both a list of wikilinks
    and a boolean indicating eligibility.
    """
    unique_links = dict()
    n_links = 0

    for row in range(n_rows):
        cell = table.cells(row, column_idx)
        # skip cells without links
        if cell is None or len(cell.wikilinks) == 0:
            continue

        # assume the first link is the only link
        link = cell.wikilinks[0]

        # links to files don't count
        if link.target.startswith("File:"):
            continue

        unique_links[link.title] = link
        n_links += 1

    # If there are no links we can return early
    if n_links == 0:
        return [], False

    # determine eligiblity
    unique_fraction = len(unique_links) / n_links
    link_fraction = n_links / n_rows

    eligibility = (
        unique_fraction > ACCEPTABLE_UNIQUE_FRACTION
        and link_fraction > ACCEPTABLE_LINK_FRACTION
    )
    return list(unique_links.values()), eligibility


def extract_table(table: wtp.Table) -> List[VideoItem]:
    """
    Extracts ListItems from a table. Again, we use some heuristics:
    - we return all the wikilinks from the first 'eligible column', where:
    - an eligible column has 'mostly' unique data
    - an eligible column has 'mostly' wikilinks
    """

    video_items = []

    n_rows = len(table.data())
    n_columns = len(table.data()[0])
    for i in range(n_columns):
        links, eligible = parse_column(table, i, n_rows)
        if eligible:
            video_items.extend(map(video_item_from_wikilink, links))
            break

    return video_items


def extract_section(section: wtp.Section) -> List[VideoItem]:
    video_items = []
    # according to docs, this weird pattern will flatten lists
    for l in section.get_lists("\*+"):
        video_items.extend(extract_list(l))

    for t in section.get_tables():
        video_items.extend(extract_table(t))

    return video_items


# Common Wikipedia sections that don't contain useful content
SECTION_BLACKLIST = ["See also", "Notes", "References"]


def extract_video_items(parsed: wtp.WikiText) -> List[VideoItem]:
    video_items = []

    for s in parsed.get_sections(include_subsections=True):
        # skip the See Also section, which can contain lists
        if s.title is not None and s.title.strip() in SECTION_BLACKLIST:
            continue
        video_items.extend(extract_section(s))

    return video_items


MAX_CHARS = 250


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


def segment_from_video_item(item: VideoItem) -> Union["vid_def.Segment", None]:
    """
    Builds a segment from the given video item.
    """
    segment_desc = clean_extract(wiki_api.get_article_extract(item.article_title))

    image_url = wiki_api.get_article_image_url(item.article_title)
    if image_url is None:
        image_url = wiki_api.get_fallback_article_image_url(item.article_title)

    # We really didn't find anything, turf this item
    if image_url is None:
        return None

    return vid_def.Segment(
        name=item.name, description=segment_desc, image_url=image_url
    )
