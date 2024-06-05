import asyncio
import inspect
import logging
import os
import re
import sys

from global_stuff import global_message_queue
from logger_code import LoggerBase


def format_sse(event: str, data: dict) -> str:
    message = f"event: {event}\ndata: {data}\n\n"
    return message

async def send_message(event: str, data: dict, logger: LoggerBase=None):
    message = format_sse(event, data,)
    asyncio.create_task(global_message_queue.put(message))
    if logger:
        # Get the previous frame in the stack, otherwise it would be this function
        func = inspect.currentframe().f_back.f_code
        logger.debug(f"send_message: {message}, called by {func.co_filename}:{func.co_firstlineno}")

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
