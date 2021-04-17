from dataclasses import dataclass
from typing import List
import random

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


@dataclass
class VideoDef:

    # The title of the video.
    title: str
    # The YouTube description of the video.
    description: str
    # A list of segments to include in the video.
    segments: List[Segment]


def video_def_from_list_url(url: str) -> VideoDef:
    article_title = wiki_parse.get_article_title_from_url(url)
    parsed = wiki_parse.parse_article_wikitext(article_title)
    video_items = wiki_parse.extract_video_items(parsed)

    # filter out pages that don't exist
    item_titles = list(map(lambda item: item.article_title, video_items))
    exist_dict = wiki_api.get_articles_exists(item_titles)
    video_items = list(filter(lambda item: exist_dict[item.article_title], video_items))

    n_segments = min(10, len(video_items))

    # secret top 10 selection algorithm
    top_items = random.sample(video_items, n_segments)

    segments = list(map(wiki_parse.segment_from_video_item, top_items))

    return segments
