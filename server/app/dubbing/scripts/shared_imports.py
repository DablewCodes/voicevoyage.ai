import os

OUTPUT_DIRECTORY = os.path.join(os.getcwd(), "app/dubbing", "Outputs")
ORIGINAL_SUBFOLDER_NAME = "video"
OUTPUT_FOLDER = os.path.join(OUTPUT_DIRECTORY, ORIGINAL_SUBFOLDER_NAME)
TEMP_WORKING_DIRECTORY = os.path.join(os.getcwd(), "app/dubbing", "workingFolder")
TEMP_SRT_DIRECTORY = os.path.join(os.getcwd(), "app/dubbing", "workingFolder/srt")
TEMP_SRT_NAME = "subtitles.srt"
TEMP_AUDIO_DIRECTORY = os.path.join(os.getcwd(), "app/dubbing", "workingFolder/audio")
TEMP_AUDIO_NAME = "audio.mp3"
TEMP_VIDEO_DIRECTORY = os.path.join(os.getcwd(), "app/dubbing", "workingFolder/video")
TEMP_VIDEO_NAME = "video.mp4"
