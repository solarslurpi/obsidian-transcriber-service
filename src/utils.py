import asyncio
import json
import logging
import os
import re
import sys
import time

from dotenv import load_dotenv
load_dotenv()

from global_stuff import global_message_queue


LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

def format_sse(event: str, data: object) -> str:
    """
    Format a Server-Sent Event (SSE) message.

    Args:
        event (str): The type of the event.
        data (object): The data to be sent, either a string (for status events) or a Pydantic model (for other events).

    Returns:
        str: A formatted SSE message string.
    """
    if isinstance(data, str):
        data_str = data
    elif isinstance(data, dict):
        data_str = json.dumps(data)
    else:
        raise ValueError(f"Invalid data type: {type(data)} Expected a string for status events or a dict for other events.")
    message = {}
    message["event"] = event
    message["data"] = data_str
    return message

def send_sse_message(event:str, data: dict):
    message = format_sse(event, data)
    # Get the current event loop, or create a new one if it doesn't exist
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # If called in a new thread where no loop is running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Check if the loop is running; if not, run the task directly
    if loop.is_running():
        asyncio.create_task(global_message_queue.put(message))
    else:
        # Run the coroutine directly and wait for it to complete
        loop.run_until_complete(global_message_queue.put(message))


def mock_info_dict():
    '''Here we attach a cache to the mock_info_dict function to avoid reading the file multiple times.'''
    if not hasattr(mock_info_dict, "_cache"):
        filepath = f"{LOCAL_DIRECTORY}/test_info_dict_KbZDsrs5roI.json"
        with open(filepath) as f:
            mock_info_dict._cache = json.load(f)
    return mock_info_dict._cache

def mock_chapters(info_dict):
    chapters_list = []
    if not hasattr(mock_chapters, "_cache"):
        chapters_list = info_dict.get('chapters', [])
        if len(chapters_list) > 0:
            # The chapters are deleted here because info_dict evolves into the metadata.
            # The chapters end up in the TranscriptionState as part of the transcription text layout.
            del info_dict['chapters']
        else:
            chapters_list = [{'start_time': 0.0, 'end_time': 0.0}]
        mock_chapters._cache = chapters_list

    return mock_chapters._cache

def mock_youtube_download(youtube_url:str, mp3_filename:str):
    time.sleep(2)
    return
def add_src_to_sys_path():
    """
    Adds the 'src' directory to sys.path if it's not already included.
    Assumes the workspace directory is the parent of the parent directory
    of the script that calls this function.
    """
    # Determine the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Assume the workspace directory is two levels up from this script directory
    workspace_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))

    # Path to the 'src' directory relative to the workspace directory
    src_path = os.path.join(workspace_dir, 'src')

    # Append the 'src' directory to sys.path if it's not already there
    if src_path not in sys.path:
        sys.path.append(src_path)

    from logger_code import LoggerBase
    logger = LoggerBase.setup_logger(__name__, logging.DEBUG)
    logger.debug(f"Added {src_path} to sys.path")

def cleaned_name(uncleaned_name:str) -> str:

    cleaned_name = re.sub(r"[^a-zA-Z0-9 \.-]", "", uncleaned_name)
    return cleaned_name.replace(" ", "_")
