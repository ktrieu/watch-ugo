from dataclasses import dataclass
from typing import List

import wiki_parse


@dataclass
class Segment:

    # The name of the item in this segment.
    name: str
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
    parsed = wiki_parse.parse_article(url)
