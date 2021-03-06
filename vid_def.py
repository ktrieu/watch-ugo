from dataclasses import dataclass
from typing import List, Union
import random

import jsonpickle

import wiki_parse
import wiki_api


@dataclass
class Segment:

    # The name of the item in this segment.
    name: str
    # The text to read while displaying this segment.
    description: str
    # The URL of the image to display in this segment.
    image_url: str
    # The URL of the article where we got the text.
    # We preserve this for citation purposes.
    article_url: str


@dataclass
class VideoDef:

    # The title of the video.
    title: str
    # A YouTube description, with attribution
    description: str
    # A list of segments to include in the video.
    segments: List[Segment]


def video_title_from_article_title(title: str, n_segments: int) -> str:
    """
    Generates a video title from an unescaped article title.
    We:
    - remove "List of" from the beginning of the title
    - capitalize the first letter
    - and add the Top {n} framing
    """
    unescaped_title = wiki_parse.unescape_article_title(title)
    unescaped_title = unescaped_title.replace("List of ", "")
    # capitalize the first letter of the unescaped title
    unescaped_title = unescaped_title[0].capitalize() + unescaped_title[1:]
    return f"Top {n_segments} {unescaped_title} of All Time"


def filter_nonexistent_video_items(
    items: List[wiki_parse.VideoItem],
) -> List[wiki_parse.VideoItem]:
    """
    Filters out video times that point to a Wikipedia article that doesn't exist.
    """
    item_titles = list(map(lambda item: item.article_title, items))
    exist_dict = wiki_api.get_articles_exists(item_titles)
    return list(
        filter(lambda item: exist_dict.get(item.article_title.lower(), False), items)
    )


def remove_duplicate_video_items(
    items: List[wiki_parse.VideoItem],
) -> List[wiki_parse.VideoItem]:
    unique_titles = dict()
    for item in items:
        unique_titles[item.article_title] = item

    return list(unique_titles.values())


def build_description(
    video_title: str, segments: List[Segment], article_url: str
) -> str:
    description = ""

    description += f"Thank you for watching our video, {video_title}!\nPlease remember to like, favorite, and subscribe for more WatchUGO content!\n\n"
    description += f"Sources:\n\nItems taken from {article_url}.\n\n"

    # the rendering code reverses the segments before rendering, so we have to do the same
    for idx, segment in enumerate(reversed(segments)):
        description += f"Number {len(segments) - idx}:\nText from {segment.article_url}\nImage from {segment.image_url}\n\n"

    return description


def video_def_from_list_url(url: str) -> VideoDef:
    article_title = wiki_parse.get_article_title_from_url(url)
    parsed = wiki_parse.parse_article_wikitext(article_title)
    video_items = wiki_parse.extract_video_items(parsed)
    video_items = filter_nonexistent_video_items(video_items)
    video_items = remove_duplicate_video_items(video_items)

    # some items may fail after fetching, in which case they return None.
    # So, we iterate through the items randomly, building at most 10.
    random.shuffle(video_items)
    segments = []

    for item in video_items:
        segment = wiki_parse.segment_from_video_item(item)
        if segment is not None:
            segments.append(segment)
        if len(segments) == 10:
            break

    video_title = video_title_from_article_title(article_title, len(segments))
    description = build_description(video_title, segments, url)
    return VideoDef(title=video_title, description=description, segments=segments)


def get_video_def_file_name(video_def: VideoDef):
    return video_def.title.replace(":", "_").replace(" ", "_")


def save_video_def(video_def: VideoDef, output_path: Union[str, None]):
    if output_path is None:
        output_path = f"{get_video_def_file_name(video_def)}.json"

    json = jsonpickle.encode(video_def, indent=True)

    with open(output_path, "w") as file:
        file.write(json)
