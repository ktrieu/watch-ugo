import tempfile

import gtts
import moviepy.editor as mpy


def tts_speak(text: str) -> mpy.AudioFileClip:
    """
    Uses Google TTS to speak `text`, and then converts that sound
    into a MoviePy AudioFileClip.
    """
    tts = gtts.gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        tts.write_to_fp(temp)
    return mpy.AudioFileClip(temp.name)
