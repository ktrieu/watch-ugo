import moviepy.editor as mpy
import moviepy.video.fx.all as vfx
import numpy as np
import PIL.ImageFilter
import PIL.Image
import jsonpickle
from moviepy.video.compositing.concatenate import concatenate_videoclips
import render_util

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
INTRO_SLATE_WAIT_SECS = 1
SEGMENT_WAIT_SECS = 0.5


def load_video_def_from_file(file_path: str) -> vid_def.VideoDef:
    with open(file_path, "r") as f:
        return jsonpickle.decode(f.read())


# We need that space between U and GO, or Google will read it wrong.
INTRO_TEXT = "Welcome back to Watch U GO. Today, we're looking at the"


def generate_intro_tts_text(video_title: str) -> str:
    return f"{INTRO_TEXT} {video_title}"


def render_intro_clip(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    intro_audio = render_util.tts_speak(generate_intro_tts_text(video_def.title))
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


def get_segment_tts(num: int, segment: vid_def.Segment) -> mpy.AudioClip:
    text = f"Number {num}: {segment.name}. {segment.description}"
    return render_util.tts_speak(text)


def blur_filter(frame):
    pil_image = PIL.Image.fromarray(frame)
    pil_image = pil_image.filter(PIL.ImageFilter.GaussianBlur(radius=50))
    blurred = np.array(pil_image)
    blurred.reshape(frame.shape)
    return blurred


def render_segment(num: int, segment: vid_def.Segment) -> mpy.VideoClip:
    audio_clip = get_segment_tts(num, segment)
    image_clip = render_util.image_download(segment.image_url).to_RGB()

    text_overlay_clip = mpy.ImageClip(OVERLAY_LOCATION)
    name_text = mpy.TextClip(
        txt=segment.name, size=SEGMENT_NAME_SIZE, font=FONT_PATH, color="white"
    ).set_position(SEGMENT_NAME_ORIGIN)

    number_text = mpy.TextClip(
        txt=f"{num}", size=NUMBER_TEXT_SIZE, font=FONT_PATH, color="white"
    ).set_position(NUMBER_TEXT_ORIGIN)

    aspect_ratio = image_clip.w / image_clip.h

    if aspect_ratio <= VIDEO_WIDTH / VIDEO_HEIGHT:
        image_clip = image_clip.resize(height=VIDEO_HEIGHT)
        image_blurred = image_clip.resize(width=VIDEO_WIDTH)
    else:
        image_clip = image_clip.resize(width=VIDEO_WIDTH)
        image_blurred = image_clip.resize(height=VIDEO_HEIGHT)

    image_clip = image_clip.set_position(("center", "center"))

    image_blurred = image_blurred.crop(
        width=VIDEO_WIDTH,
        height=VIDEO_HEIGHT,
        x_center=image_blurred.w / 2,
        y_center=image_blurred.h / 2,
    ).fl_image(blur_filter)

    return (
        mpy.CompositeVideoClip(
            [image_blurred, image_clip, text_overlay_clip, name_text, number_text],
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
        )
        .set_duration(audio_clip.duration + SEGMENT_WAIT_SECS)
        .set_fps(24)
        .set_audio(audio_clip)
    )


def render_video_def(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    intro_clip = render_intro_clip(video_def)

    segment_clips = []
    for idx, segment in enumerate(video_def.segments):
        segment_clip = render_segment(idx + 1, segment)
        segment_clip.save_frame(f"{idx}.png")
        segment_clips.append(segment_clip)

    final_video = concatenate_videoclips([intro_clip, *reversed(segment_clips)])

    return final_video


def save_file(path: str, clip: mpy.VideoClip):
    clip.write_videofile(path, threads=8)
