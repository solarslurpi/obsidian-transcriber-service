import asyncio
import json
import logging
import os
from typing import Dict

import app.logging_config

from app.service.message_queue_manager import MessageQueueManager

global task
# Create a logger instance for this module
logger = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    if not isinstance(seconds, (int, float)):
        return "0:00:00"
    total_seconds = int(seconds)
    mins, secs = divmod(total_seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

def format_sse(event: str, data: object) -> Dict:
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


async def send_sse_message(queue: MessageQueueManager, event: str, data: dict):
    message = format_sse(event, data)
    await queue.add_message(message)
    await asyncio.sleep(0.1)

def get_audio_directory():
    audio_directory = 'audio' # Hardcoded...
    workspace_directory = os.getcwd()
    full_path_to_audio = os.path.join(workspace_directory, audio_directory)
    # Create the directory if it does not exist
    os.makedirs(full_path_to_audio, exist_ok=True)
    logger.debug(f"Ensured audio directory exists at: {full_path_to_audio}")
    return full_path_to_audio
