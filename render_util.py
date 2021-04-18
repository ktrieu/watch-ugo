import tempfile
import gtts
import moviepy.editor as mpy
import requests
import PIL.ImageFile
import PIL.Image

import temp

# HACK: Tell PIL to just load slightly damaged images
PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True


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


def image_download(url: str):
    """
    Downloads the image at URL and saves it into a
    ImageClip.
    """
    response = requests.get(url)

    with temp.get_temp_file() as temp_file:
        temp_file.write(response.content)

    # add a background to images that don't have one
    image = PIL.Image.open(temp_file.name).convert("RGBA")
    bg = PIL.Image.new("RGBA", image.size, (255, 255, 255, 255))
    with_background = PIL.Image.alpha_composite(bg, image).save(
        temp_file.name, format="png"
    )

    return mpy.ImageClip(temp_file.name)