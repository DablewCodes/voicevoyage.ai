from pytube import YouTube
from .shared_imports import TEMP_VIDEO_DIRECTORY, TEMP_VIDEO_NAME


def get_video_from_youtube(video_link: str) -> int:
    yt = YouTube(video_link)
    yt = yt.streams.get_highest_resolution()
    yt.download(output_path=TEMP_VIDEO_DIRECTORY, filename=TEMP_VIDEO_NAME)

    return 0