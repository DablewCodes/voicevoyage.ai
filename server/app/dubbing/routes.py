from flask import render_template, request, jsonify, send_file
from app.dubbing import bp
from iso639 import Lang
from .scripts.srt import parse_srt_file
from .scripts.translate import translate_dictionary
from .scripts.TTS import synthesize_dictionary_async
from .scripts.audio_builder import build_audio
from .scripts.transcription import get_transcription
from .scripts.conversion_to_audio import convert_video_to_audio
from .scripts.shared_imports import *
from .scripts.video_from_youtube import get_video_from_youtube
from .scripts.utilities import cleanup_dirs
import copy
import asyncio
from .. import socketio
import subprocess
from elevenlabs.client import ElevenLabs
import random


@bp.route("/")
def index():
    return render_template("dubbing/index.html")


@bp.route("/get_dubbing", methods=["POST"])
def get_dubbing():
    if request.method == "POST":
        # Send socketio message for showing progress, current step: processing input
        socketio.emit(
            "processing_update", "2"
        )
        cleanup_dirs()  # Cleanup the temporary working directories and remove residual files for handling the new request

        target_language_code = Lang(
            (request.form.get("targetLanguage"))
        ).pt1  # e.g. Converting "English" to "en"

        voices_dict = {
            "Rachel": "8pyds607JOdOCI41ULhQ", 
            "Joanne": "B7q7pSAWZ2gJEI8va3ZO", 
            "Clyde": "VcqLbSZtZl3YIs6Z6zqF",
            "Clone": ""
            #"Natasha": "kWXzaxptiBKRNkhDMbJs",
            #"Alex": "QyK5aj9xfhradDCm76Cr",
            #"Jack": "6PyH33USyYEhOIS79wwi",
        }
        target_voice = voices_dict[str(request.form.get("targetVoice"))]

        if request.form.get(
            "videoURL"
        ):  # Check if the dubbing is for a YouTube video, and get it's audio stream if yes
            video_url = str(request.form.get("videoURL"))
            try:
                get_video_from_youtube(video_url)
            except Exception as e:
                print(
                    "An error occured while getting the audio stream from the YouTube video: {}".format(
                        str(e)
                    )
                )
                return jsonify({"error": str(e)}), 500
            try:
                convert_video_to_audio()
            except Exception as e:
                print(
                    "An error occured while converting the saved YouTube video to audio: {}".format(
                        str(e)
                    )
                )
                return jsonify({"error": str(e)}), 500
            # video_id = video_url[video_url.find(".be/") + 4 :] if "youtu.be" in video_url else video_url[video_url.find("?v=") + 3 :]

        else:  # Handle the user uploaded file
            uploaded_file = request.files["uploadedFile"]

            if uploaded_file.filename.endswith(
                ".srt"
            ):  # If the uploaded file is a subtitles file, read
                try:
                    srt_text = uploaded_file.read().decode("utf-8-sig", "replace")
                except Exception as e:
                    print(
                        "An error occurred while parsing the uploaded subtitles file: {}".format(
                            str(e)
                        )
                    )
                    return jsonify({"error": str(e)}), 500

            elif uploaded_file.filename.endswith(
                ".mp4"
            ):  # If uploaded file is a video, save locally, and then convert to audio
                try:
                    uploaded_file.save(
                        os.path.join(TEMP_VIDEO_DIRECTORY, TEMP_VIDEO_NAME)
                    )
                except Exception as e:
                    print(
                        "An error occured while saving the video file on the server: {}".format(
                            str(e)
                        )
                    )
                    return jsonify({"error": str(e)}), 500
                try:
                    convert_video_to_audio()
                except Exception as e:
                    print(
                        "An error occured while converting the saved video to audio: {}".format(
                            str(e)
                        )
                    )
                    return jsonify({"error": str(e)}), 500

            elif uploaded_file.filename.endswith(
                ".mp3"
            ):  # If uploaded file is an audio, save locally
                try:
                    uploaded_file.save(
                        os.path.join(TEMP_AUDIO_DIRECTORY, TEMP_AUDIO_NAME)
                    )
                except Exception as e:
                    print(
                        "An error occured while saving the audio file on the server: {}".format(
                            str(e)
                        )
                    )
                    return jsonify({"error": str(e)}), 500

            else:
                print("An unsupported format file has been uploaded")
                return (
                    jsonify({"error": "An unsupported format file has been uploaded"}),
                    500,
                )
            
        
        # At this stage, if the user upload/input was a video/audio file or YouTube url, \
        # there should be a audio file present in the designated temporary location to be\
        # processed, so we transcribe it to get the subtitles
        if os.path.join(
            TEMP_AUDIO_DIRECTORY, TEMP_AUDIO_NAME
        ):  
            try:
                socketio.emit(
                    "processing_update", "3"
                )  # Send socketio message for showing progress, current step: transcription
                transcription = get_transcription()
            except Exception as e:
                print(
                    "An error occured while transcribing the audio file: {}".format(
                        str(e)
                    )
                )
                return jsonify({"error": str(e)}), 500

            try:
                with open(
                    transcription, "r", encoding="utf-8-sig", errors="replace"
                ) as file:
                    srt_text = file.read()
            except Exception as e:
                print(
                    "An error occured while reading the generated subtitles file: {}".format(
                        str(e)
                    )
                )
                return jsonify({"error": str(e)}), 500

        # This srt_text will either be from the topmost 'if' condition where we checked if the uploaded file was an srt or \
        # generated from the transcription step in the previous code block
        srt_dict = parse_srt_file(
            srt_text.split("\n")
        )  
        total_audio_length = int(srt_dict[str(len(srt_dict))]["end_ms"])
        max_chars = max(len(entry['text']) for entry in srt_dict.values())

        try:
            #pass
            #output_file = process_language(srt_dict, target_language_code, target_voice, total_audio_length)
            output_file = process_language(srt_dict, target_language_code, target_voice, total_audio_length, max_chars)
            return send_file(output_file,as_attachment=True,mimetype="audio/mpeg")
        except Exception as e:
            error_message = (
                "Error occurred while processing the dubbing request: {}".format(str(e))
            )
            return jsonify({"error": error_message}), 500


def process_language(
    srt_dict: dict,
    target_language_code: str,
    target_voice: str,
    total_audio_length: int,
    max_chars= 150,
) -> str:
    individualLanguageSubsDict = copy.deepcopy(srt_dict)

    # Send socketio message for showing progress, current step: translation
    socketio.emit("processing_update", "4")
    #individualLanguageSubsDict = translate_dictionary(individualLanguageSubsDict, target_language_code)
    individualLanguageSubsDict = translate_dictionary(individualLanguageSubsDict, target_language_code, max_chars=max_chars)

    # Send socketio message for showing progress, current step: tts

    client = ElevenLabs(
    api_key=os.environ.get("ELEVENLABS_API_KEY"), # Defaults to ELEVEN_API_KEY
    )

    voice = client.clone(
    name="myVoice{}".format(random.randint(1,10)),
    description="Clone voice", # Optional
    files=[os.path.join(TEMP_AUDIO_DIRECTORY, TEMP_AUDIO_NAME)])

    response = client.voices.get_all()
    
    socketio.emit("processing_update", "5")
    individualLanguageSubsDict = asyncio.run(
        synthesize_dictionary_async(individualLanguageSubsDict, response.voices[-1].voice_id)
    )

    # Send socketio message for showing progress, current step: sync
    socketio.emit("processing_update", "6")
    output_file = build_audio(individualLanguageSubsDict, total_audio_length)
    #command = "python app/dubbing/scripts/wav2lip/inference.py --checkpoint_path /home/wajahat/Workspace/voicevoyage.ai/server/app/dubbing/scripts/wav2lip/checkpoints/wav2lip.pth --outfile {} --face {} --audio {}".format(os.path.join(OUTPUT_FOLDER, "result.mp4"), os.path.join(TEMP_VIDEO_DIRECTORY, TEMP_VIDEO_NAME), os.path.join(OUTPUT_FOLDER, "audio.wav"))
    #print(command)
    #script_directory = "/home/wajahat/Workspace/voicevoyage.ai/server/app/dubbing/scripts/wav2lip"
    #result = subprocess.run(command, shell=True, capture_output=True, text=True)
    #result = subprocess.run(command, shell=True, cwd=script_directory)
    #os.system(command)
    # Print the output of the command
    #print("Standard Output:", result.stdout)
    #print("Standard Error:", result.stderr)
    #print("Return Code:", result.returncode)

    # Send socketio message for showing progress, current step: done
    socketio.emit("processing_update", "7")
    return output_file
    #return os.path.join(OUTPUT_FOLDER, ORIGINAL_SUBFOLDER_NAME, "result.mp4")
