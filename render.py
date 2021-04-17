import moviepy.editor as mpy
import jsonpickle
import voice

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


# We need that space between U and GO, or Google will read it wrong.
INTRO_TEXT = "Welcome back to Watch U GO. Today, we're looking at the"


def generate_intro_text(video_title: str) -> str:
    return f"{INTRO_TEXT} {video_title}"


def render_intro_clip(video_def: vid_def.VideoDef) -> mpy.VideoClip:
    intro_audio = voice.tts_speak(generate_intro_text(video_def.title))
    intro_bg = mpy.ColorClip((VIDEO_WIDTH, VIDEO_HEIGHT))

    intro_clip = mpy.CompositeVideoClip([intro_bg])
    intro_clip = (
        intro_clip.set_audio(intro_audio).set_duration(intro_audio.duration).set_fps(24)
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
