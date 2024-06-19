import soundfile
import pyrubberband
import pathlib
import os
import io
import numpy as np
from .shared_imports import *
import math
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import langcodes
import subprocess

# Set working folder
workingFolder = TEMP_WORKING_DIRECTORY


def trim_clip(inputSound):
    trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
    trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
    strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))
    strippedSound = strip_silence(inputSound)
    return strippedSound

# Function to insert audio into canvas at specific point
def insert_audio(canvas, audioToOverlay, startTimeMs):
    # Create a copy of the canvas
    canvasCopy = canvas
    # Overlay the audio onto the copy
    canvasCopy = canvasCopy.overlay(audioToOverlay, position=int(startTimeMs))
    # Return the copy
    return canvasCopy

# Function to create a canvas of a specific duration in miliseconds
def create_canvas(canvasDuration, frame_rate):
    canvas = AudioSegment.silent(duration=canvasDuration, frame_rate=frame_rate)
    return canvas

def get_speed_factor(subsDict, trimmedAudio, desiredDuration, num):
    virtualTempFile = AudioSegment.from_file(trimmedAudio, format="wav")
    rawDuration = virtualTempFile.duration_seconds
    trimmedAudio.seek(0) # This MUST be done to reset the file pointer to the start of the file, otherwise will get errors next time try to access the virtual files
    # Calculate the speed factor, put into dictionary
    desiredDuration = float(desiredDuration)
    speedFactor = (rawDuration*1000) / desiredDuration
    subsDict[num]['speed_factor'] = speedFactor
    return subsDict

def stretch_audio(audioFileToStretch, speedFactor, num):
    virtualTempAudioFile = io.BytesIO()
    # Write the raw string to virtualtempaudiofile
    y, sampleRate = soundfile.read(audioFileToStretch)

    streched_audio = pyrubberband.time_stretch(y, sampleRate, speedFactor, rbargs={'--fine': '--fine'}) # Need to add rbarges in weird way because it demands a dictionary of two values
    #soundfile.write(f'{workingFolder}\\temp_stretched.wav', streched_audio, sampleRate)
    soundfile.write(virtualTempAudioFile, streched_audio, sampleRate, format='wav')
    #return AudioSegment.from_file(f'{workingFolder}\\temp_stretched.wav', format="wav")
    return AudioSegment.from_file(virtualTempAudioFile, format="wav")

def stretch_with_rubberband(y, sampleRate, speedFactor):
    rubberband_streched_audio = pyrubberband.time_stretch(y, sampleRate, speedFactor, rbargs={'--fine': '--fine'}) # Need to add rbarges in weird way because it demands a dictionary of two values
    return rubberband_streched_audio

def stretch_with_ffmpeg(audioInput, speed_factor):
    min_speed_factor = 0.5
    max_speed_factor = 100.0
    filter_loop_count = 1

    # Validate speed_factor and calculate filter_loop_count
    if speed_factor < min_speed_factor:
        filter_loop_count = math.ceil(math.log(speed_factor) / math.log(min_speed_factor))
        speed_factor = speed_factor ** (1 / filter_loop_count)
        if speed_factor < 0.001:
            raise ValueError(f"ERROR: Speed factor is extremely low, and likely an error. It was: {speed_factor}")
    elif speed_factor > max_speed_factor:
        raise ValueError(f"ERROR: Speed factor cannot be over 100. It was {speed_factor}.")

    # Prepare ffmpeg command
    command = ['ffmpeg', '-i', 'pipe:0', '-filter:a', f'atempo={speed_factor}', '-f', 'wav', 'pipe:1']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Pass the audio data to ffmpeg and read the processed data
    out, err = process.communicate(input=audioInput.getvalue())

    # Check for errors
    if process.returncode != 0:
        raise Exception(f'ffmpeg error: {err.decode()}')

    # Convert the output bytes to a NumPy array to be compatible with rest of the program
    # audio_data = numpy.frombuffer(out, numpy.int16)
    # Convert to float64 (which is the format used by pyrubberband)
    # audio_data = audio_data.astype(numpy.float64)
    # # Normalize the data to the range of float64 audio
    # audio_data /= numpy.iinfo(numpy.int16).max

    return out # Returns bytes

def stretch_audio_clip(audioFileToStretch, speedFactor, mode="ffmpeg"):
    virtualTempAudioFile = io.BytesIO()
    # Write the raw string to virtualtempaudiofile
    audioObj, sampleRate = soundfile.read(audioFileToStretch) # auddioObj is a numpy array
    
    # Stretch the audio using user specified method
    if mode == 'ffmpeg':
        stretched_audio = stretch_with_ffmpeg(audioFileToStretch, speedFactor)
        virtualTempAudioFile.write(stretched_audio)
    elif mode == 'rubberband':
        stretched_audio = stretch_with_rubberband(audioObj, sampleRate, speedFactor)
        #soundfile.write(f'{workingFolder}\\temp_stretched.wav', streched_audio, sampleRate)
        soundfile.write(virtualTempAudioFile, stretched_audio, sampleRate, format='wav')
    #return AudioSegment.from_file(f'{workingFolder}\\temp_stretched.wav', format="wav")
    return AudioSegment.from_file(virtualTempAudioFile, format="wav")

def build_audio(subsDict, totalAudioLength, sampling_rate="24000", output_format="wav", audio_encoding="mp3", twoPassVoiceSynth = False ):

    virtualTrimmedFileDict = {}
    # First trim silence off the audio files
    for key, value in subsDict.items():
        filePathTrimmed = os.path.join(workingFolder,  str(key)) + "_t.wav"
        subsDict[key]['TTS_FilePath_Trimmed'] = filePathTrimmed

        # Trim the clip and re-write file
        rawClip = AudioSegment.from_file(value['TTS_FilePath'], format="mp3", frame_rate=sampling_rate)
        trimmedClip = trim_clip(rawClip)

        # Create virtual file in dictionary with audio to be read later
        tempTrimmedFile = io.BytesIO()
        trimmedClip.export(tempTrimmedFile, format="wav")
        virtualTrimmedFileDict[key] = tempTrimmedFile
        keyIndex = list(subsDict.keys()).index(key)
        print(f" Trimmed Audio: {keyIndex+1} of {len(subsDict)}", end="\r")
    print("\n")

    # Calculates speed factor if necessary. Azure doesn't need this, so skip it
    # Calculate speed factors for each clip, aka how much to stretch the audio
    for key, value in subsDict.items():
        #subsDict = get_speed_factor(subsDict, value['TTS_FilePath_Trimmed'], value['duration_ms'], num=key)
        subsDict = get_speed_factor(subsDict, virtualTrimmedFileDict[key], value['duration_ms'], num=key)
        keyIndex = list(subsDict.keys()).index(key)
        print(f" Calculated Speed Factor: {keyIndex+1} of {len(subsDict)}", end="\r")
    print("\n")

    # If two pass voice synth is enabled, have API re-synthesize the clips at the new speed
    # Azure allows direct specification of audio duration, so no need to re-synthesize
    #if twoPassVoiceSynth == True:
    #    subsDict = TTS.synthesize_dictionary( subsDict, audio_encoding, secondPass=True)
            
    #    for key, value in subsDict.items():
    #        # Trim the clip and re-write file
    #        rawClip = AudioSegment.from_file(value['TTS_FilePath'], format="mp3", frame_rate=int(sampling_rate))
    #        trimmedClip = trim_clip(rawClip)
    #        trimmedClip.export(virtualTrimmedFileDict[key], format="wav")
    #        keyIndex = list(subsDict.keys()).index(key)
    #        print(f" Trimmed Audio (2nd Pass): {keyIndex+1} of {len(subsDict)}", end="\r")
    #    print("\n")

    # Create canvas to overlay audio onto
    canvas = create_canvas(totalAudioLength, int(sampling_rate))

    # Stretch audio and insert into canvas
    for key, value in subsDict.items():
        #stretchedClip = AudioSegment.from_file(value['TTS_FilePath_Trimmed'], format="wav")

        #NOT ORIGINAL LINE
        stretchedClip = stretch_audio_clip(virtualTrimmedFileDict[key], speedFactor=subsDict[key]['speed_factor'])
        # Original LINES ------------------------------------------------
        #stretchedClip = AudioSegment.from_file(virtualTrimmedFileDict[key], format="wav")
        #virtualTrimmedFileDict[key].seek(0) # Not 100% sure if this is necessary but it was in the other place it is used

        print("Audio Stretch loop pass")

        canvas = insert_audio(canvas, stretchedClip, value['start_ms'])
        keyIndex = list(subsDict.keys()).index(key)
        print(f" Final Audio Processed: {keyIndex+1} of {len(subsDict)}", end="\r")
    print("\n")

    # Use video file name to use in the name of the output file. Add language name and language code
    outputFileName = "audio."
    # Set output path
    outputFileName = os.path.join(OUTPUT_FOLDER, outputFileName)

    # Determine string to use for output format and file extension based on config setting
    outputFormat=output_format.lower()
    if outputFormat == "mp3":
        outputFileName += "mp3"
        formatString = "mp3"
    elif outputFormat == "wav":
        outputFileName += "wav"
        formatString = "wav"
    elif outputFormat == "aac":
        #outputFileName += "m4a"
        #formatString = "mp4" # Pydub doesn't accept "aac" as a format, so we have to use "mp4" instead. Alternatively, could use "adts" with file extension "aac"
        outputFileName += "aac"
        formatString = "adts" # Pydub doesn't accept "aac" as a format, so we have to use "mp4" instead. Alternatively, could use "adts" with file extension "aac"

    canvas = canvas.set_channels(2) # Change from mono to stereo
    try:
        print("\nExporting audio file...")
        canvas.export(outputFileName, format=formatString, bitrate="192k")
    except:
        outputFileName = outputFileName + ".bak"
        canvas.export(outputFileName, format=formatString, bitrate="192k")
        print("\nThere was an issue exporting the audio, it might be a permission error. The file was saved as a backup with the extension .bak")
        print("Try removing the .bak extension then listen to the file to see if it worked.\n")

    return outputFileName
