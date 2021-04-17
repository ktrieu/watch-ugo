import os

import gtts
import moviepy.editor as mpy

import temp


def tts_speak(text: str) -> mpy.AudioFileClip:
    """
    Uses Google TTS to speak `text`, and then converts that sound
    into a MoviePy AudioFileClip.
    """
    tts = gtts.gTTS(text)
    with temp.get_temp_file() as temp_file:
        tts.write_to_fp(temp_file)
    clip = mpy.AudioFileClip(temp_file.name)
    return clip