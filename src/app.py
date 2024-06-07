


import asyncio
import os
import logging
from typing import Optional

from fastapi import FastAPI,  Request, Form, UploadFile
from sse_starlette import EventSourceResponse

from global_stuff import global_message_queue
from logger_code import LoggerBase
from process_check import process_check
from audio_processing_model import AudioProcessRequest
from utils import send_message



app = FastAPI()
# Set up logging filte
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

logger_one = logging.getLogger('router_code')
logger_one.setLevel(logging.DEBUG)


@app.post("/api/v1/process_audio")
async def init_process_audio(youtube_url: Optional[str] = Form(None),
                             file: Optional[UploadFile] = Form(None),
                             audio_quality: str = Form("default")):

    err_msg = ''
    try:
        audio_input = AudioProcessRequest(
            youtube_url=youtube_url,
            file=file,
            audio_quality=audio_quality
        )
        logger.debug(f"app.init_process_audio: Audio input: {audio_input}")
    except Exception as e:
        err_msg = f"error: {e}"
        send_message(err_msg,logger)


    try:
        asyncio.create_task(process_check(audio_input))
    except Exception as e:
        err_msg = f"error: {e}"
        send_message(err_msg,logger)

    return f"status: {err_msg}"



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
    logger.debug("app.event_generator: Starting SSE event generator.")
    while True:
        if await request.is_disconnected():
            break
        message = await global_message_queue.get()
        logger.debug("app.event_generator: Message received from the queue.")
        # Just in case the message is an empty string or None.
        if message:
            logger.debug(f"app.event_generator: Message: **{message}**")
            # yield f"data: {message}\n\n"  # Correct SSE format
            yield "data: hello\n\n"

@app.get("/api/v1/health")
async def health_check():
    logger.debug("app.health_check: Health check endpoint accessed.")
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
