import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

import app.logging_config
from app.routes.cancel_endpoint import cleanup_task

RETRY_TIMEOUT = 3000

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/sse")
async def sse_endpoint(
    request: Request
):
    return EventSourceResponse(event_generator(request))


async def event_generator(request: Request):
    queue = request.app.state.message_queue_manager
    message_id_counter = 0
    while True:
        if await request.is_disconnected():
            break
        # WAIT FOR MESSAGE
        try:
            # The wait for a message might be a long time. In this case, unblock so other pieces of the code can run.
            message = await asyncio.wait_for(queue.get_message(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for message from queue")
            continue
        except asyncio.CancelledError:
            logger.info("Task was cancelled")
            await cleanup_task(request.app.state.task, request.app.state.message_queue_manager)
            # Perform any necessary cleanup here
            break  # Exit the loop on cancellation
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break  # Exit the loop on unexpected error
        # PROCESS MESSAGE
        try:
            event = message['event']
            data = message['data']
            if event == "server-error" or (event == "data" and data == 'done'):
                break

            # Just in case the message is an empty string or None.
            if message:
                info = data
                if event == "data":
                # FOR DEBUGGING START
                    dict_data = json.loads(data)
                    key = next(iter(dict_data), None)
                    if key not in ['num_chapters', 'basename', 'key']:
                        info = key
                    if key == 'chapter':
                        chapter_data = dict_data["chapter"]
                        info = f"chapter{chapter_data['number']}{chapter_data['text'][:200]}"
                logger.debug(f"--> SENDING MESSAGE. Event: {event}, Info: {info}")
                # FOR DEBUGGING STOP
                message_id_counter += 1
                yield {
                    "event": event,
                    "id": str(message_id_counter),
                    "retry": RETRY_TIMEOUT,
                    "data": data
                }
        except asyncio.CancelledError:
            logger.info("Task was cancelled")
            await cleanup_task(request.app.state.task, request.app.state.message_queue_manager)
            # Perform any necessary cleanup here
            break  # Exit the loop on cancellation
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Key Error processing message: {message}", exc_info=e)
        except Exception as e:
            logger.error(f"Unexpected error processing message: {message}", exc_info=e)
