import gtts
import moviepy.editor as mpy
import requests

import temp

TTS_SPEEDUP = 1.2


def tts_speak(text: str) -> mpy.AudioFileClip:
    """
    Uses Google TTS to speak `text`, and then converts that sound
    into a MoviePy AudioFileClip.
    """
    tts = gtts.gTTS(text)
    with temp.get_temp_file() as temp_file:
        tts.write_to_fp(temp_file)
    # the TTS voice talks a little slow, so we speed it up slightly
    clip = mpy.AudioFileClip(temp_file.name).fl_time(lambda t: TTS_SPEEDUP * t)
    return clip


def image_download(url: str):
    """
    Downloads the image at URL and saves it into a
    ImageClip.
    """
    response = requests.get(url)

    with temp.get_temp_file() as temp_file:
        temp_file.write(response.content)

    return mpy.ImageClip(temp_file.name)