import moviepy.editor as mpy
import jsonpickle

import vid_def

# We're aiming for 1080p on YouTube
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Landmarks for text insertion, in (top left), (top right) format
NUMBER_TEXT_BOX = ((122, 95), (248, 221))
SEGMENT_NAME_BOX = ((113, 875), (912, 986))


def load_video_def_from_file(file_path: str) -> vid_def.VideoDef:
    with open(file_path, "r") as f:
        return jsonpickle.decode(f.read())


def render_intro_clip(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    return None


def render_segment(segment: vid_def.Segment) -> mpy.VideoClip:
    return None


def render_video_def(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    intro_clip = render_intro_clip(video_def)

    segment_clips = list(map(render_segment, video_def.segments))

    final_video = mpy.concatenate_videoclips([intro_clip, *segment_clips])

    return final_video


def save_file(path: str, clip: mpy.VideoClip):
    clip.write_videofile(path)
