import tempfile
import os

"""
Since moviepy needs the audio files to exist for the duration of the program,
this module wraps the tempfile module, keeps the files open,
and then deletes them all when asked to.
"""

tempfiles = []


def get_temp_file():
    temp = tempfile.NamedTemporaryFile(delete=False)
    tempfiles.append(temp.name)
    return temp


def remove_all_temp_files():
    for f in tempfiles:
        os.remove(f)