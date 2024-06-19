import re

def parse_srt_file(srtFileLines, line_buffer=0, preTranslated=False):
    # Matches the following example with regex:    00:00:20,130 --> 00:00:23,419
    subtitleTimeLineRegex = re.compile(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d')

    # Create a dictionary
    subsDict = {}

    # Will add this many milliseconds of extra silence before and after each audio clip / spoken subtitle line
    addBufferMilliseconds = int(line_buffer)

    # Enumerate lines, and if a line in lines contains only an integer, put that number in the key, and a dictionary in the value
    # The dictionary contains the start, ending, and duration of the subtitles as well as the text
    # The next line uses the syntax HH:MM:SS,MMM --> HH:MM:SS,MMM . Get the difference between the two times and put that in the dictionary
    # For the line after that, put the text in the dictionary
    for lineNum, line in enumerate(srtFileLines):
        line = line.strip()
        if line.isdigit() and subtitleTimeLineRegex.match(srtFileLines[lineNum + 1]):
            lineWithTimestamps = srtFileLines[lineNum + 1].strip()
            lineWithSubtitleText = srtFileLines[lineNum + 2].strip()

            # If there are more lines after the subtitle text, add them to the text
            count = 3
            while True:
                # Check if the next line is blank or not
                if (lineNum+count) < len(srtFileLines) and srtFileLines[lineNum + count].strip():
                    lineWithSubtitleText += ' ' + srtFileLines[lineNum + count].strip()
                    count += 1
                else:
                    break

            # Create empty dictionary with keys for start and end times and subtitle text
            subsDict[line] = {'start_ms': '', 'end_ms': '', 'duration_ms': '', 'text': '', 'break_until_next': '', 'srt_timestamps_line': lineWithTimestamps}

            time = lineWithTimestamps.split(' --> ')
            time1 = time[0].split(':')
            time2 = time[1].split(':')

            # Converts the time to milliseconds
            processedTime1 = int(time1[0]) * 3600000 + int(time1[1]) * 60000 + int(time1[2].split(',')[0]) * 1000 + int(time1[2].split(',')[1]) #/ 1000 #Uncomment to turn into seconds
            processedTime2 = int(time2[0]) * 3600000 + int(time2[1]) * 60000 + int(time2[2].split(',')[0]) * 1000 + int(time2[2].split(',')[1]) #/ 1000 #Uncomment to turn into seconds
            timeDifferenceMs = str(processedTime2 - processedTime1)

            # Adjust times with buffer
            if addBufferMilliseconds > 0 and not preTranslated:
                subsDict[line]['start_ms_buffered'] = str(processedTime1 + addBufferMilliseconds)
                subsDict[line]['end_ms_buffered'] = str(processedTime2 - addBufferMilliseconds)
                subsDict[line]['duration_ms_buffered'] = str((processedTime2 - addBufferMilliseconds) - (processedTime1 + addBufferMilliseconds))
            else:
                subsDict[line]['start_ms_buffered'] = str(processedTime1)
                subsDict[line]['end_ms_buffered'] = str(processedTime2)
                subsDict[line]['duration_ms_buffered'] = str(processedTime2 - processedTime1)
            
            # Set the keys in the dictionary to the values
            subsDict[line]['start_ms'] = str(processedTime1)
            subsDict[line]['end_ms'] = str(processedTime2)
            subsDict[line]['duration_ms'] = timeDifferenceMs
            subsDict[line]['text'] = lineWithSubtitleText
            if lineNum > 0:
                # Goes back to previous line's dictionary and writes difference in time to current line
                subsDict[str(int(line)-1)]['break_until_next'] = processedTime1 - int(subsDict[str(int(line) - 1)]['end_ms'])
            else:
                subsDict[line]['break_until_next'] = 0


    # Apply the buffer to the start and end times by setting copying over the buffer values to main values
    if addBufferMilliseconds > 0 and not preTranslated:
        for key, value in subsDict.items():
            subsDict[key]['start_ms'] = value['start_ms_buffered']
            subsDict[key]['end_ms'] = value['end_ms_buffered']
            subsDict[key]['duration_ms'] = value['duration_ms_buffered']

    return subsDict