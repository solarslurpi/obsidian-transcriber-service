


import asyncio
import json
import logging
from typing import Optional

from fastapi import FastAPI,  Request, Form, UploadFile, HTTPException
from pydantic import ValidationError
from sse_starlette import EventSourceResponse

from global_stuff import global_message_queue
from logger_code import LoggerBase
from process_check import process_check
from audio_processing_model import AudioProcessRequest
from utils import format_sse

MESSAGE_STREAM_RETRY_TIMEOUT = 3000

app = FastAPI()
# Set up logging filte
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

logger_one = logging.getLogger('router_code')
logger_one.setLevel(logging.DEBUG)


@app.post("/api/v1/process_audio")
async def init_process_audio(youtube_url: Optional[str] = Form(None),
                             file: Optional[UploadFile] = Form(None),
                             audio_quality: str = Form("default")):

    try:
        audio_input = AudioProcessRequest(
            youtube_url=youtube_url,
            file=None,
            audio_quality=audio_quality
        )
    except ValidationError as e:
        # Pydantic ValidationError has its own structure for errors.
        error_msg = e.errors()[0].get('msg','msg attribute not found')
        message = format_sse("error", error_msg)
        asyncio.create_task(global_message_queue.put(message))
        # Wait for the message to be sent by the async generator
        while not global_message_queue.empty():
            await asyncio.sleep(0.1)
        raise HTTPException(status_code=400, detail=e.errors())

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

    # create_task is run in its own event loop, meaning Exceptions occur outside the main event loop
    # where the current code is executing.This is why the error is not caught by the try-except block.
    asyncio.create_task(process_check(audio_input))


    return f"status: Transcription process has started."



@app.get("/api/v1/sse")
async def sse_endpoint(request: Request):
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get('user-agent', 'unknown')

    logger.debug(f"app.get.sse: Request received: {method} {url} from {client_ip}")
    logger.debug(f"app.get.sse: User-Agent: {user_agent}")

    return EventSourceResponse(event_generator(request))

async def event_generator(request: Request):
    id_cnt = 1
    logger.debug("app.event_generator: Starting SSE event generator.")
    while True:
        if await request.is_disconnected():
            break
        message = await global_message_queue.get()
        logger.debug("app.event_generator: Message received from the queue.")
        # Just in case the message is an empty string or None.
        if message:
            logger.debug(f"app.event_generator: Message: **{message}**")
            yield {
                "event":message.get('event', 'unknown'),
                "id": id_cnt,
                "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                "data": message.get('data', 'No data found.')
            }
            id_cnt += 1
            yield message

@app.get("/api/v1/health")
async def health_check():
    logger.debug("app.health_check: Health check endpoint accessed.")
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
