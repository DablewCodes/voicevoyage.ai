#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Imports
#from .auth import GOOGLE_TRANSLATE_API
from .auth import gcp_authentication
from .shared_imports import OUTPUT_DIRECTORY
import re
import sys
import os
from operator import itemgetter
import copy
import langcodes
import html

GOOGLE_TTS_API, GOOGLE_TRANSLATE_API = gcp_authentication()

#======================================== Translate Text ================================================
# Note: This function was almost entirely written by GPT-3 after feeding it my original code and asking it to change it so it
# would break up the text into chunks if it was too long. It appears to work

def process_response_text(text, targetLanguage):
    text = html.unescape(text)
    #text = remove_notranslate_tags(text)
    #text = replace_manual_translations(text, targetLanguage)
    return text

def split_transcript_chunks(text, max_length=5000):
    # Calculate the total number of utf-8 codepoints
    #totalCodepoints = len(text.encode("utf-8"))
    
    # Split the transcript into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Initialize a list to store the chunks of text
    chunks = []
    
    # Initialize a string to store a chunk of text
    chunk = ""
    
    # For each sentence in the list of sentences
    for sentence in sentences:
        # If adding the sentence to the chunk would keep it within the maximum length
        if len(chunk.encode("utf-8")) + len(sentence.encode("utf-8")) + 1 <= max_length:  # Adding 1 to account for space
            # Add the sentence to the chunk
            chunk += sentence + " "
        else:
            # If adding the sentence would exceed the maximum length and chunk is not empty
            if chunk:
                # Add the chunk to the list of chunks
                chunks.append(chunk.strip())
            # Start a new chunk with the current sentence
            chunk = sentence + " "
    
    # Add the last chunk to the list of chunks (if it's not empty)
    if chunk:
        chunks.append(chunk.strip())
    
    # Return the list of chunks
    return chunks

def convertChunkListToCompatibleDict(chunkList):
    # Create dictionary with numbers as keys and chunks as values
    chunkDict = {}
    for i, chunk in enumerate(chunkList, 1):
        chunkDict[i] = {'text': chunk}
    return chunkDict


# Translate the text entries of the dictionary
def translate_dictionary(inputSubsDict, target_language_code, org_lang="en-US", max_chars=150, skipTranslation=False, transcriptMode=False):

    targetLanguage = target_language_code
    translateService = "google"
    formality = "default"

    # Create a container for all the text to be translated
    textToTranslate = []


    for key in inputSubsDict:
        originalText = inputSubsDict[key]['text']
        # Add the text to the list of text to be translated
        textToTranslate.append(originalText)
   
    # Calculate the total number of utf-8 codepoints
    codepoints = 0
    for text in textToTranslate:
        codepoints += len(text.encode("utf-8"))
    
    # If the codepoints are greater than 28000, split the request into multiple
    # Google's API limit is 30000 Utf-8 codepoints per request, while DeepL's is 130000, but we leave some room just in case
    if skipTranslation == False:
        if translateService == 'google' and codepoints > 27000:
            # GPT-3 Description of what the following line does:
            # If Google Translate is being used:
            # Splits the list of text to be translated into smaller chunks of 100 texts.
            # It does this by looping over the list in steps of 100, and slicing out each chunk from the original list. 
            # Each chunk is appended to a new list, chunkedTexts, which then contains the text to be translated in chunks.
            # The same thing is done for DeepL, but the chunk size is 400 instead of 100.
            chunkSize = 100 if translateService == 'google' else 400
            chunkedTexts = [textToTranslate[x:x+chunkSize] for x in range(0, len(textToTranslate), chunkSize)]
            
            # Send and receive the batch requests
            for j,chunk in enumerate(chunkedTexts):
                
                # Send the request
                if translateService == 'google':
                    # Print status with progress
                    print(f'[Google] Translating text group {j+1} of {len(chunkedTexts)}')
                    response = GOOGLE_TRANSLATE_API.projects().translateText(
                        parent='projects/' + str(os.environ.get("GOOGLE_PROJECT_ID")),
                        body={
                            'contents': chunk,
                            'sourceLanguageCode': org_lang,
                            'targetLanguageCode': targetLanguage,
                            'mimeType': 'text/html',
                            #'model': 'nmt',
                            #'glossaryConfig': {}
                        }
                    ).execute()

                    # Extract the translated texts from the response
                    translatedTexts = [process_response_text(response['translations'][i]['translatedText'], targetLanguage) for i in range(len(response['translations']))]

                    # Add the translated texts to the dictionary
                    # Divide the dictionary into chunks of 100
                    for i in range(chunkSize):
                        key = str((i+1+j*chunkSize))
                        inputSubsDict[key]['translated_text'] = process_response_text(translatedTexts[i], targetLanguage)
                        # Print progress, ovwerwrite the same line
                        print(f' Translated with Google: {key} of {len(inputSubsDict)}', end='\r')
                else:
                    print("Error: Invalid translate_service setting. Only 'google' and 'deepl' are supported.")
                    sys.exit()
                
        else:
            if translateService == 'google':
                print("Translating text using Google...")
                response = GOOGLE_TRANSLATE_API.projects().translateText(
                    parent='projects/' + str(os.environ.get("GOOGLE_PROJECT_ID")),
                    body={
                        'contents':textToTranslate,
                        'sourceLanguageCode': org_lang,
                        'targetLanguageCode': targetLanguage,
                        'mimeType': 'text/html',
                        #'model': 'nmt',
                        #'glossaryConfig': {}
                    }
                ).execute()
                translatedTexts = [process_response_text(response['translations'][i]['translatedText'], targetLanguage) for i in range(len(response['translations']))]
                
                # Add the translated texts to the dictionary
                for i, key in enumerate(inputSubsDict):
                    inputSubsDict[key]['translated_text'] = process_response_text(translatedTexts[i], targetLanguage)
                    # Print progress, overwrite the same line
                    print(f' Translated: {key} of {len(inputSubsDict)}', end='\r')
            else:
                print("Error: Invalid translate_service setting. Only 'google' and 'deepl' are supported.")
                sys.exit()
    else:
        for key in inputSubsDict:
            inputSubsDict[key]['translated_text'] = process_response_text(inputSubsDict[key]['text'], targetLanguage) # Skips translating, such as for testing

    
    # If translating transcript, return the translated text
    if transcriptMode:
        return inputSubsDict

    # # Debug export inputSubsDict as json for offline testing
    # import json
    # with open('inputSubsDict.json', 'w') as f:
    #     json.dump(inputSubsDict, f)

    # # DEBUG import inputSubsDict from json for offline testing
    # import json
    # with open('inputSubsDict.json', 'r') as f:
    #     inputSubsDict = json.load(f)

    combinedProcessedDict = combine_subtitles_advanced(inputSubsDict, int(max_chars))

    if skipTranslation == False:
        # Use video file name to use in the name of the translate srt file, also display regular language name
        lang = langcodes.get(targetLanguage).display_name()
        
        translatedSrtFileName = "Translated" + f" - {lang} - {targetLanguage}.srt"
        # Set path to save translated srt file
        translatedSrtFileName = os.path.join(OUTPUT_DIRECTORY, translatedSrtFileName)
        # Write new srt file with translated text
        with open(translatedSrtFileName, 'w', encoding='utf-8-sig') as f:
            for key in combinedProcessedDict:
                f.write(str(key) + '\n')
                f.write(combinedProcessedDict[key]['srt_timestamps_line'] + '\n')
                f.write(combinedProcessedDict[key]['translated_text'] + '\n')
                f.write('\n')

    return combinedProcessedDict


##### Add additional info to the dictionary for each language #####
def set_translation_info(languageBatchDict):

    newBatchSettingsDict = copy.deepcopy(languageBatchDict)

    # If using Google, set all languages to use Google in dictionary
    for langNum, langInfo in languageBatchDict.items():
        newBatchSettingsDict[langNum]['translate_service'] = 'google'
        newBatchSettingsDict[langNum]['formality'] = None

    return newBatchSettingsDict    


#======================================== Combine Subtitle Lines ================================================
def combine_subtitles_advanced(inputDict, maxCharacters=200):
    charRateGoal = 20 #20
    gapThreshold = 100 # The maximum gap between subtitles to combine
    noMorePossibleCombines = False
    # Convert dictionary to list of dictionaries of the values
    entryList = []

    for key, value in inputDict.items():
        value['originalIndex'] = int(key)-1
        entryList.append(value)

    while not noMorePossibleCombines:
        entryList, noMorePossibleCombines = combine_single_pass(entryList, charRateGoal, gapThreshold, maxCharacters)

    # Convert the list back to a dictionary then return it
    return dict(enumerate(entryList, start=1))

def combine_single_pass(entryListLocal, charRateGoal, gapThreshold, maxCharacters):
    # Want to restart the loop if a change is made, so use this variable, otherwise break only if the end is reached
    reachedEndOfList = False
    noMorePossibleCombines = True # Will be set to False if a combination is made

    # Use while loop because the list is being modified
    while not reachedEndOfList:

        # Need to update original index in here
        for entry in entryListLocal:
            entry['originalIndex'] = entryListLocal.index(entry)

        # Will use later to check if an entry is the last one in the list, because the last entry will have originalIndex equal to the length of the list - 1
        originalNumberOfEntries = len(entryListLocal)

        # Need to calculate the char_rate for each entry, any time something changes, so put it at the top of this loop
        entryListLocal = calc_list_speaking_rates(entryListLocal, charRateGoal)

        # Sort the list by the difference in speaking speed from charRateGoal
        priorityOrderedList = sorted(entryListLocal, key=itemgetter('char_rate_diff'), reverse=True) 

        # Iterates through the list in order of priority, and uses that index to operate on entryListLocal
        # For loop is broken after a combination is made, so that the list can be re-sorted and re-iterated
        for progress, data in enumerate(priorityOrderedList):
            i = data['originalIndex']
            # Check if last entry, and therefore will end loop when done with this iteration
            if progress == len(priorityOrderedList) - 1:
                reachedEndOfList = True

            # Check if the current entry is outside the upper and lower bounds
            if (data['char_rate'] > charRateGoal or data['char_rate'] < charRateGoal):

                # Check if the entry is the first in entryListLocal, if so do not consider the previous entry
                if data['originalIndex'] == 0:
                    considerPrev = False
                else:
                    considerPrev = True

                # Check if the entry is the last in entryListLocal, if so do not consider the next entry
                if data['originalIndex'] == originalNumberOfEntries - 1:
                    considerNext = False
                else:
                    considerNext = True

                # Check if current entry is still in the list - if it has been combined with another entry, it will not be

                
                # Get the char_rate of the next and previous entries, if they exist, and calculate the difference
                # If the diff is positive, then it is lower than the current char_rate
                try:
                    nextCharRate = entryListLocal[i+1]['char_rate']
                    nextDiff = data['char_rate'] - nextCharRate
                except IndexError:
                    considerNext = False
                    nextCharRate = None
                    nextDiff = None
                try:
                    prevCharRate = entryListLocal[i-1]['char_rate']
                    prevDiff = data['char_rate'] - prevCharRate
                except IndexError:
                    considerPrev = False
                    prevCharRate = None
                    prevDiff = None
                    
            else:
                continue

            # Define functions for combining with previous or next entries - Generated with copilot, it's possible this isn't perfect
            def combine_with_next():
                entryListLocal[i]['text'] = entryListLocal[i]['text'] + ' ' + entryListLocal[i+1]['text']
                entryListLocal[i]['translated_text'] = entryListLocal[i]['translated_text'] + ' ' + entryListLocal[i+1]['translated_text']
                entryListLocal[i]['end_ms'] = entryListLocal[i+1]['end_ms']
                entryListLocal[i]['end_ms_buffered'] = entryListLocal[i+1]['end_ms_buffered']
                entryListLocal[i]['duration_ms'] = int(entryListLocal[i+1]['end_ms']) - int(entryListLocal[i]['start_ms'])
                entryListLocal[i]['duration_ms_buffered'] = int(entryListLocal[i+1]['end_ms_buffered']) - int(entryListLocal[i]['start_ms_buffered'])
                entryListLocal[i]['srt_timestamps_line'] = entryListLocal[i]['srt_timestamps_line'].split(' --> ')[0] + ' --> ' + entryListLocal[i+1]['srt_timestamps_line'].split(' --> ')[1]
                del entryListLocal[i+1]

            def combine_with_prev():
                entryListLocal[i-1]['text'] = entryListLocal[i-1]['text'] + ' ' + entryListLocal[i]['text']
                entryListLocal[i-1]['translated_text'] = entryListLocal[i-1]['translated_text'] + ' ' + entryListLocal[i]['translated_text']
                entryListLocal[i-1]['end_ms'] = entryListLocal[i]['end_ms']
                entryListLocal[i-1]['end_ms_buffered'] = entryListLocal[i]['end_ms_buffered']
                entryListLocal[i-1]['duration_ms'] = int(entryListLocal[i]['end_ms']) - int(entryListLocal[i-1]['start_ms'])
                entryListLocal[i-1]['duration_ms_buffered'] = int(entryListLocal[i]['end_ms_buffered']) - int(entryListLocal[i-1]['start_ms_buffered'])
                entryListLocal[i-1]['srt_timestamps_line'] = entryListLocal[i-1]['srt_timestamps_line'].split(' --> ')[0] + ' --> ' + entryListLocal[i]['srt_timestamps_line'].split(' --> ')[1]
                del entryListLocal[i]


            # Choose whether to consider next and previous entries, and if neither then continue to next loop
            if data['char_rate'] > charRateGoal:
                # Check to ensure next/previous rates are lower than current rate, and the combined entry is not too long, and the gap between entries is not too large
                # Need to add check for considerNext and considerPrev first, because if run other checks when there is no next/prev value to check, it will throw an error
                if considerNext == False or nextDiff or nextDiff < 0 or (entryListLocal[i]['break_until_next'] >= gapThreshold) or (len(entryListLocal[i]['translated_text']) + len(entryListLocal[i+1]['translated_text']) > maxCharacters):
                    considerNext = False
                try:
                    if considerPrev == False or not prevDiff or prevDiff < 0 or (entryListLocal[i-1]['break_until_next'] >= gapThreshold) or (len(entryListLocal[i-1]['translated_text']) + len(entryListLocal[i]['translated_text']) > maxCharacters):
                        considerPrev = False
                except TypeError:
                    considerPrev = False

            elif data['char_rate'] < charRateGoal:
                # Check to ensure next/previous rates are higher than current rate
                if considerNext == False or not nextDiff or nextDiff > 0 or (entryListLocal[i]['break_until_next'] >= gapThreshold) or (len(entryListLocal[i]['translated_text']) + len(entryListLocal[i+1]['translated_text']) > maxCharacters):
                    considerNext = False
                try:
                    if considerPrev == False or not prevDiff or prevDiff > 0 or (entryListLocal[i-1]['break_until_next'] >= gapThreshold) or (len(entryListLocal[i-1]['translated_text']) + len(entryListLocal[i]['translated_text']) > maxCharacters):
                        considerPrev = False
                except TypeError:
                    considerPrev = False
            else:
                continue

            # Continue to next loop if neither are considered
            if not considerNext and not considerPrev:
                continue

            # Should only reach this point if two entries are to be combined
            if data['char_rate'] > charRateGoal:
                # If both are to be considered, then choose the one with the lower char_rate
                if considerNext and considerPrev:
                    if nextDiff < prevDiff:
                        combine_with_next()
                        noMorePossibleCombines = False
                        break
                    else:
                        combine_with_prev()
                        noMorePossibleCombines = False
                        break
                # If only one is to be considered, then combine with that one
                elif considerNext:
                    combine_with_next()
                    noMorePossibleCombines = False
                    break
                elif considerPrev:
                    combine_with_prev()
                    noMorePossibleCombines = False
                    break
                else:
                    print(f"Error U: Should not reach this point! Current entry = {i}")
                    print(f"Current Entry Text = {data['text']}")
                    continue
            
            elif data['char_rate'] < charRateGoal:
                # If both are to be considered, then choose the one with the higher char_rate
                if considerNext and considerPrev:
                    if nextDiff > prevDiff:
                        combine_with_next()
                        noMorePossibleCombines = False
                        break
                    else:
                        combine_with_prev()
                        noMorePossibleCombines = False
                        break
                # If only one is to be considered, then combine with that one
                elif considerNext:
                    combine_with_next()
                    noMorePossibleCombines = False
                    break
                elif considerPrev:
                    combine_with_prev()
                    noMorePossibleCombines = False
                    break
                else:
                    print(f"Error L: Should not reach this point! Index = {i}")
                    print(f"Current Entry Text = {data['text']}")
                    continue
    return entryListLocal, noMorePossibleCombines

#-- End of combine_single_pass --    

#----------------------------------------------------------------------

# Calculate the number of characters per second for each subtitle entry
def calc_dict_speaking_rates(inputDict, dictKey='translated_text'):  
    tempDict = copy.deepcopy(inputDict)
    for key, value in tempDict.items():
        tempDict[key]['char_rate'] = round(len(value[dictKey]) / (int(value['duration_ms']) / 1000), 2)
    return tempDict

def calc_list_speaking_rates(inputList, charRateGoal, dictKey='translated_text'): 
    tempList = copy.deepcopy(inputList)
    for i in range(len(tempList)):
        # Calculate the number of characters per second based on the duration of the entry
        tempList[i]['char_rate'] = round(len(tempList[i][dictKey]) / (int(tempList[i]['duration_ms']) / 1000), 2)
        # Calculate the difference between the current char_rate and the goal char_rate - Absolute Value
        tempList[i]['char_rate_diff'] = abs(round(tempList[i]['char_rate'] - charRateGoal, 2))
    return tempList