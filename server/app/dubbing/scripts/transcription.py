import whisper
import os
from whisper.utils import get_writer
from .shared_imports import (
    TEMP_SRT_DIRECTORY,
    TEMP_SRT_NAME,
    TEMP_AUDIO_DIRECTORY,
    TEMP_AUDIO_NAME,
)


def get_transcription(audio_file=TEMP_AUDIO_NAME, model_name="tiny.en") -> str:
    model = whisper.load_model(model_name, download_root="models")
    path_to_audio = os.path.join(TEMP_AUDIO_DIRECTORY, audio_file)
    result = model.transcribe(path_to_audio, language="en")

    # Save as an SRT file
    srt_writer = get_writer("srt", TEMP_SRT_DIRECTORY)
    srt_writer(result, TEMP_SRT_NAME)

    return os.path.join(TEMP_SRT_DIRECTORY, TEMP_SRT_NAME)
