import glob
import os
from .shared_imports import TEMP_AUDIO_DIRECTORY, TEMP_SRT_DIRECTORY, TEMP_VIDEO_DIRECTORY

def cleanup_dirs():

    directory_to_ext_dict  = {TEMP_AUDIO_DIRECTORY: ".mp3",
                            TEMP_SRT_DIRECTORY: ".srt",
                            TEMP_VIDEO_DIRECTORY: ".mp4"}

    for directory in directory_to_ext_dict:
        for filename in glob.glob( os.path.join(directory, "*"+directory_to_ext_dict[directory])):
            #print(filename)
            os.remove(filename)