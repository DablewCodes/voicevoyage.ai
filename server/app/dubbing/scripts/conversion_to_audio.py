import subprocess
from .shared_imports import (
    TEMP_AUDIO_DIRECTORY,
    TEMP_AUDIO_NAME,
    TEMP_VIDEO_DIRECTORY,
    TEMP_VIDEO_NAME,
)
import os


def convert_video_to_audio() -> int:
    command = "ffmpeg -i {} -vn -ar 44100 -ac 2 -b:a 192k {}".format(
        os.path.join(TEMP_VIDEO_DIRECTORY, TEMP_VIDEO_NAME),
        os.path.join(TEMP_AUDIO_DIRECTORY, TEMP_AUDIO_NAME),
    )
    subprocess.call(command, shell=True)

    return 0
