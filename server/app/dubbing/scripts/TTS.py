import json
import os
import asyncio
import aiohttp
from .shared_imports import TEMP_WORKING_DIRECTORY, TEMP_AUDIO_DIRECTORY, TEMP_AUDIO_NAME
from elevenlabs.client import ElevenLabs

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

async def synthesize_text_elevenlabs_async_http(text, voiceID, modelID, apiKey=ELEVENLABS_API_KEY):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voiceID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": apiKey
    }
    data = {
        "text": text,
        "model_id": modelID,
        # "voice_settings": {
        #     "stability": 0.5,
        #     "similarity_boost": 0.5
        # }
    }
    
    audio_bytes = b''  # Initialize an empty bytes object

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    audio_bytes += chunk
            else:
                try:
                    error_message = await response.text()
                    error_dict = json.loads(error_message)
                    print(f"\n\nERROR: ElevenLabs API returned code: {response.status}  -  {response.reason}")
                    print(f" - Returned Error Status: {error_dict['detail']['status']}")
                    print(f" - Returned Error Message: {error_dict['detail']['message']}")
                    
                    # Handle specific errors:
                    if error_dict['detail']['status'] == "invalid_uid" or error_dict['detail']['status'] == "voice_not_found":
                        print("    > You may have forgotten to set the voice name in batch.ini to an Elevenlabs Voice ID. The above message should tell you what invalid voice is currently set.")
                        print("    > See this article for how to find a voice ID: https://help.elevenlabs.io/hc/en-us/articles/14599760033937-How-do-I-find-my-voices-ID-of-my-voices-via-the-website-and-through-the-API-")
                except KeyError:
                    if response.status == 401:
                        print("  > ElevenLabs did not accept the API key or you are unauthorized to use that voice.")
                        print("  > Did you set the correct ElevenLabs API key in the cloud_service_settings.ini file?\n")
                    elif response.status == 400:
                        print("  > Did you set the correct ElevenLabs API key in the cloud_service_settings.ini file?\n")
                    elif response.status == 429:
                        print("  > You may have exceeded the ElevenLabs API rate limit. Did you set the 'elevenlabs_max_concurrent' setting too high for your plan?\n")
                except Exception as ex:
                    print(f"ElevenLabs API error occurred.\n")
                return None

    return audio_bytes

async def synthesize_dictionary_async(subsDict, target_voice, voice_model="eleven_multilingual_v2" ,skipSynthesize=False, max_concurrent_jobs=2, secondPass=False):
    semaphore = asyncio.Semaphore(max_concurrent_jobs)
    lock = asyncio.Lock()
    progress = 0
    total_tasks = len(subsDict)
    errorsOccured = False

    print("Beginning TTS Synthesis...")
    async def synthesize_and_save(key, value):
        nonlocal progress
        
        # Update and display progress
        async with lock:
            progress += 1
            print(f" Synthesizing TTS: {progress} of {total_tasks}", end="\r")
            
        # Use this to set max concurrent jobs
        async with semaphore:
            audio = await synthesize_text_elevenlabs_async_http(
                value['translated_text'], 
                target_voice, 
                voice_model
            )

            if audio:
                filePath = os.path.join(TEMP_WORKING_DIRECTORY, f'{str(key)}.mp3')
                with open(filePath, "wb") as out:
                    out.write(audio)
                subsDict[key]['TTS_FilePath'] = filePath
            else:
                nonlocal errorsOccured
                errorsOccured = True
                subsDict[key]['TTS_FilePath'] = "Failed"

    tasks = []

    for key, value in subsDict.items():
        if not skipSynthesize: #and cloudConfig['tts_service'] == "elevenlabs":
            task = asyncio.create_task(synthesize_and_save(key, value))
            tasks.append(task)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    print("                                        ") # Clear the line
    
    # If errors occurred, tell user
    if errorsOccured:
        print("Warning: Errors occurred during TTS synthesis. Please check any error messages above for details.")
    else:
        print("Synthesis Finished")
    return subsDict