'''Test receipt of expected SSE messages from the server.
data: {data: title}
data: {data: frontmatter}
data: {data: num_chapters}
data: {data: chapter}
data: {data: done}'''
import logging
import pytest
import requests
import threading

from unittest.mock import patch, AsyncMock
from dotenv import load_dotenv
load_dotenv()


from .test_utils import audio_input, info_dict, logger, mock_metadata
from logger_code import LoggerBase
from metadata_extractor_code import MetadataExtractor
from transcription_state_code import initialize_transcription_state



@patch.object(MetadataExtractor, 'extract_metadata')
def mock_extract_metadata(mock_method):
    return mock_metadata

mock_extract_metadata()


# This test should probably focus just on the metadata components of the transcript. then we can focus on sending the chapters.
# Test metadata. test chapters. test with obsidian client. step back. make todos for shipping.

@pytest.mark.asyncio
async def test_building_transcript(mocker, audio_input, mock_metadata, logger):
    try:
        # Set up the sse connection.
        thread = threading.Thread(target=handle_sse, args=(logger,))
        thread.start()
        # Set up the return metadata.
        test_metadata = mock_metadata
        # The method that returns an instance of the Metadata class is mocked.
        mocker.patch.object(MetadataExtractor, 'extract_metadata', new_callable=AsyncMock, return_value=test_metadata)

    except Exception as e:
        logger.error(f"Error mocking metadata extractor: {e}")
        return




    # This method sends sse messages for up to the actual transcripts of the chapters.
    state = await initialize_transcription_state(audio_input)
    logger.debug(f'test_sse_build_transcript.test_building_transcript: \n--------\nState = {state.model_dump_json(indent=4)}')


def handle_sse(logger):
    logger.debug("-->Starting SSE connection")
    payload = {}
    headers = {'accept': 'application/json'}
    url = f"http://127.0.0.1:8000/api/v1/sse"
    logger.debug(f"Sending GET request to {url}")

    response = requests.request("GET", url, headers=headers, data=payload, stream=True)

    event_type = None
    data_lines = []

    for line in response.iter_lines():
        if len(line) == 0:
            # End of an event, process the event
            if data_lines:
                handle_event(event_type, data_lines, logger)
            # Reset for the next event
            event_type = None
            data_lines = []
        else:
            line = line.decode('utf-8')
            logger.debug(f" ****{line}****")
            if line.startswith('event:'):
                event_type = line.split(': ', 1)[1]
            elif line.startswith('data:'):
                data_lines.append(line[5:].strip())
            elif line.startswith('id:'):
                event_id = line.split(': ', 1)[1]
            elif line.startswith('retry:'):
                retry_timeout = line.split(': ', 1)[1]
            elif line.strip() == '':
                # End of an event, process the event
                if data_lines:
                    handle_event(event_type, data_lines, logger)
                # Reset for the next event
                event_type = None
                data_lines = []


def handle_event(event_type, data_lines, logger):
    data = "\n".join(data_lines)
    logger.info(f"Event: {event_type if event_type else 'message'}")
    logger.info(f"Data: {data}")
