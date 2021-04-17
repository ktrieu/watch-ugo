import moviepy.editor as mpy
import jsonpickle
import voice

import vid_def

# We're aiming for 1080p on YouTube
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# File locations
OVERLAY_LOCATION = "img/watchugo_text_overlay.png"
INTRO_SLATE_LOCATION = "img/watchugo_intro_slate.png"

FONT_PATH = "KronaOne-Regular.ttf"

# Landmarks for text insertion
NUMBER_TEXT_ORIGIN = (122, 95)
NUMBER_TEXT_SIZE = (126, 126)
SEGMENT_NAME_ORIGIN = (113, 875)
SEGMENT_NAME_SIZE = (799, 111)

INTRO_SLATE_TEXT_ORIGIN = (147, 462)
INTRO_SLATE_TEXT_SIZE = (1626, 216)

# Timing constnats
INTRO_SLATE_WAIT_SECS = 2


def load_video_def_from_file(file_path: str) -> vid_def.VideoDef:
    with open(file_path, "r") as f:
        return jsonpickle.decode(f.read())


# We need that space between U and GO, or Google will read it wrong.
INTRO_TEXT = "Welcome back to Watch U GO. Today, we're looking at the"


def generate_intro_tts_text(video_title: str) -> str:
    return f"{INTRO_TEXT} {video_title}"


def render_intro_clip(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    intro_audio = voice.tts_speak(generate_intro_tts_text(video_def.title))
    intro_img = mpy.ImageClip(INTRO_SLATE_LOCATION)

    intro_text = mpy.TextClip(
        txt=video_def.title, size=INTRO_SLATE_TEXT_SIZE, font=FONT_PATH, color="black"
    ).set_position(INTRO_SLATE_TEXT_ORIGIN)

    intro_clip = (
        mpy.CompositeVideoClip([intro_img, intro_text])
        .set_duration((intro_audio.duration + INTRO_SLATE_WAIT_SECS))
        .set_fps(24)
        .set_audio(intro_audio)
    )

    return intro_clip


def render_segment(segment: vid_def.Segment) -> mpy.VideoClip:
    return None


def render_video_def(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    intro_clip = render_intro_clip(video_def)

    # segment_clips = list(map(render_segment, video_def.segments))

    final_video = intro_clip

    return final_video


def save_file(path: str, clip: mpy.VideoClip):
    clip.write_videofile(path)
