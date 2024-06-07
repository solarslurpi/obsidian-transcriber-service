'''The data messages that must be received by the client include:

data: {data: basefilename}
data: {data: frontmatter}
data: {data: num_chapters}
data: {data: chapter}
data: {data: done}

the goal of this test is to verify the client got these and to hammer out the process of building the transcript considering the fields can come in asynchronously.



'''

import json
import logging
import os
import requests

from dotenv import load_dotenv
load_dotenv()
# The actual name of the directory/folder holding file writes
LOCAL = os.getenv("LOCAL_DIRECTORY")

we_are_here = os.getcwd() # e.g.: 'C:\\Users\\happy\\Documents\\Projects\\obsidian-transcriber-service'
LOCAL_DIRECTORY = f"{we_are_here}/{LOCAL}"

from audio_processing_model import AudioProcessRequest
from logger_code import LoggerBase
from metadata_code import MetadataExtractor
from transcription_state_code import TranscriptionState

logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)

def extract_youtube_metadata(url):
    audio_input = AudioProcessRequest(youtube_url=url, audio_quality="default")
    extractor = MetadataExtractor()
    metadata, chapters = extractor.extract_metadata(audio_input)
    return metadata, chapters

metadata, chapters = extract_youtube_metadata("https://www.youtube.com/watch?v=KbZDsrs5roI")
def initialize_state():
    # Read in the metadata for "id": "KbZDsrs5roI" from test_metadata.json.
    # Now start filling in a TranscriptionState instance.  The metadata has the chapters field.
    # this field gets separated out into the individual Chapters instances part of the TranscriptionState instance.  local_mp3 is None in this case because the input is a youtube_url. So set that. set transcription_time to a random float.  ignore the hf_properties.
    def read_metadatas(filename):
        filepath = f"{LOCAL_DIRECTORY}/{filename}"
        with open(filepath) as f:
            metadatas = json.load(f)
        return metadatas
    def get_metadata(id, metadatas):
        for metadata in metadatas:
            if metadata["id"] == id:
                return metadata
        return metadatas[id]
    metadatas = read_metadatas("test_metadata.json")
    metadata = get_metadata("KbZDsrs5roI", metadatas)


    transcription_state = TranscriptionState()
    transcription_state.local_mp3 = None
    transcription_state.transcription_time = 34.0


    if "chapters" in metadata:
        chapters = metadata["chapters"]
        for chapter in chapters:
            chapter_instance = Chapter(title=chapter["title"],start=chapter["start_time"],end=chapter["end_time"],transcription=None)
            transcription_state.chapters.append(chapter_instance)
    return transcription_state

state = initialize_state()

def update_state():
    logger.debug('update_state: Start of messge handling.')
    def update_state(message):
        logger.debug(f"update_state: Message received: {message}")
        if 'basename' in message:
            # Handle basename message
            basename = message['basename']
            # Do something with basename

        elif 'chapters' in message:
            # Handle chapters message
            chapters = message['chapters']
            # Do something with chapters

        else:
            # Handle other messages
            # Do something with other messages
            pass


def handle_sse():
    payload = {}
    headers = {
    'accept': 'application/json'
    }
    url = f"http://127.0.0.1:8000/api/v1/sse"
    logger.debug.log(f"Sending GET request to {url}")

    response = requests.request("GET", url, headers=headers, data=payload, stream=True)

    event_data = ""
    # SSE is a streaming protocol.
    for line in response.iter_lines():
        update_state(line)
        print(f"Event data: {event_data}")

def post_to_process_audio():
    url = "http://127.0.0.1:8000/api/v1/process_audio"
    files=[]
    payload = {'youtube_url': 'https://www.youtube.com/watch?v=KbZDsrs5roI',
    'audio_quality': 'default'}
    headers = {
    'accept': 'application/json'
    }
    print('before post')
    response = requests.post(url, headers=headers, data=payload)
    print('after post')
    return response





def test_receive_transcript():
    # Step 1: Set up SSE
    handle_sse()

    #The goal of this test is to receive the transcript components  from the `https://www.youtube.com/watch?v=KbZDsrs5roI` YouTube Url.
    # Transcript messages:
    # data: {data: basefilename}
    # data: {data: frontmatter}
    # data: {data: num_chapters}
    # data: {data: chapter}
    # data: {data: done}

    # The test starts by sending out the two HTTP requests to the endpoints.  The POST request is sent to the `/api/v1/process_audio` endpoint with the YouTube URL and audio quality.  The GET request is sent to the `/api/v1/sse` endpoint to receive the transcript messages.  The test then processes the transcript messages and prints them out.  The test is successful if the transcript messages are received and printed out.
    pass