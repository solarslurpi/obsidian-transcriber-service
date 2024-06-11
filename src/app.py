
import asyncio
from dotenv import load_dotenv
load_dotenv()
import logging
import os
from typing import Optional



from fastapi import FastAPI, Request, File, Form, UploadFile
from sse_starlette import EventSourceResponse
from pydantic import ValidationError


from global_stuff import global_message_queue
from logger_code import LoggerBase
from process_check_code import process_check
from audio_processing_model import AudioProcessRequest
from exceptions_code import handle_exception

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists

RETRY_TIMEOUT = 3000 # For sending SSE messages

app = FastAPI()
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

@app.post("/api/v1/process_audio")
async def init_process_audio(youtube_url: Optional[str] = Form(None),
                             file: UploadFile = File(None),
                             audio_quality: str = Form("default")):
    mp3_file = None
    if file.file and not youtube_url:
        mp3_file = save_local_mp3(file)
    try:
        audio_input = AudioProcessRequest(
            youtube_url=youtube_url,
            mp3_file=mp3_file,
            audio_quality=audio_quality
        )
    except ValueError as e:
        raise await handle_exception(e, 400, e.errors())
    # Tasks run as an independent coroutine, and should handle its errors.
    asyncio.create_task(process_check(audio_input))
    return {"status": "Transcription process has started."}

def save_local_mp3(upload_file: UploadFile):
    # Ensure the local directory exists
    if not os.path.exists(LOCAL_DIRECTORY):
        os.makedirs(LOCAL_DIRECTORY)

    file_location = os.path.join(LOCAL_DIRECTORY, upload_file.filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(upload_file.file.read())
        file_object.close()
    logger.debug(f"audio_processing_model.save_local_mp3: File saved to {file_location}")
    return file_location


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
        try:
            event = message.event
            data = message.data
            logger.debug(f"app.event_generator: Message received from the queue. Event: {event}, Data: {data}")
            # Just in case the message is an empty string or None.
            if message:
                yield {
                    "event": event,
                    "id": "message_id",
                    "retry": RETRY_TIMEOUT,
                    "data": data
                }
        except:
            pass



@app.get("/api/v1/health")
async def health_check():
    logger.debug("app.health_check: Health check endpoint accessed.")
    return {"status": "ok"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)