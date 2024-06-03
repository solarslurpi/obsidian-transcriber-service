import asyncio
import logging
import os
import sys

from global_stuff import global_message_queue

def format_sse(event: str, data: dict) -> str:
    message = f"event: {event}\ndata: {data}\n\n"
    return message

def handle_error_message(data: str):
    message = format_sse("error", data)
    asyncio.create_task(global_message_queue.put(message))
    raise ValueError(data)

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
