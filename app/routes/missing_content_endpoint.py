from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import List
import logging

from app.service.message_queue_manager import MessageQueueManager
from app.service.transcription_state_code import TranscriptionStatesSingleton
from app.service.utils import send_sse_message
from app.service.process_audio import send_sse_data_messages
from app.service.exceptions_code import MissingContentException

class MissingContent(BaseModel):
    key: str
    missing_contents: List[str]

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/missing_content")
async def missing_content(
      request: Request,
      missing_content: MissingContent,
    ):
    queue = request.app.state.message_queue_manager
    logger.debug(f"Received missing content list: {missing_content}")
    try:
        states = TranscriptionStatesSingleton.get_states()
        state = states.get_state(missing_content.key)
        if not state:
            error_message = f"No state found for key: {missing_content.key}. Do not know what content is wanted."
            await send_sse_message(queue, "server-error", error_message)
            raise KeyError(error_message)
    except KeyError as e:
        return {"status": f"Error processing missing content. Error: {e}"}

    try:
        # The missing_content prop is perhaps most useful for testing.
        # Understanding whether a missing_content event has been sent.
        await send_sse_data_messages(queue, state, missing_content.missing_contents)
    except MissingContentException as e:
        error_message = f"Error processing missing content. Error: {e}"
        await send_sse_message(queue, "server-error", error_message)
        return {"status": error_message}

    return {"status": f"{', '.join(missing_content.missing_contents)}"}