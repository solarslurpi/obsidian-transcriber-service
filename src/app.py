
import asyncio
from dotenv import load_dotenv
load_dotenv()
import logging
import os
from typing import Optional, List



from fastapi import FastAPI, Request, File, Form, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette import EventSourceResponse


from exceptions_code import MissingContentException
from global_stuff import global_message_queue
from logger_code import LoggerBase
from process_check_code import process_check, send_sse_data_messages
from audio_processing_model import AudioProcessRequest
from transcription_state_code import TranscriptionStates
from utils import send_sse_message

from mock_event_generator import mock_event_generator

# initialize global access to state storage.

states = TranscriptionStates()

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists

RETRY_TIMEOUT = 3000 # For sending SSE messages

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class MissingContent(BaseModel):
    key: str
    missing_contents: List[str]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/process_audio")
async def init_process_audio(youtube_url: Optional[str] = Form(None),
                             file: UploadFile = File(None),
                             audio_quality: str = Form("default")):
    if youtube_url and file:
        raise HTTPException(status_code=400, detail="Both youtube_url and file cannot have values.")
    if not youtube_url and not file:
        raise HTTPException(status_code=400, detail="Need either a YouTube URL or mp3 file.")
    mp3_file = None
    if file is not None:
        mp3_file = save_local_mp3(file)
    try:
        audio_input = AudioProcessRequest(
            youtube_url=youtube_url,
            mp3_file=mp3_file,
            audio_quality=audio_quality
        )
    except ValueError as e:
        await send_sse_message("server-error", str(e))
        return {"status": f"Error processing audio. Error: {e}"}
    # Tasks run as an independent coroutine, and should handle its errors.

    asyncio.create_task(process_check(audio_input))
    return {"status": "Transcription process has started."}

@app.post("/api/v1/missing_content")
# Body(...) tells fastapi that the input is json. It will then validate the input again the MissingContentRequest model.  If the input does not match the model, an error will be returned.
async def missing_content(missing_content: MissingContent):
    logger.debug(f"app.missing_content: Missing content list received: {missing_content}")
    try:
        state = states.get_state(missing_content.key)
        if not state:
            await send_sse_message("server-error", f"No state found for key: {missing_content.key}.  Do not know what content is wanted.")
            raise KeyError(f"No state found for key: {missing_content.key}")
    except KeyError as e:
        return {"status": f"Error processing missing content. Error {e}"}
    try:
        # the missing_content prop is perhaps most useful for testing.  Understanding whethe a missing_content event has been sent.
        await send_sse_data_messages(state, missing_content.missing_contents)
    except MissingContentException as e:
        await send_sse_message("server-error", f"Error processing missing content. Error: {e}")
        return {"status": f"Error processing missing content. Error: {e}"}
    return {"status": f"{', '.join(missing_content.missing_contents)}"}



@app.get("/api/v1/sse")
async def sse_endpoint(request: Request):
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get('user-agent', 'unknown')

    logger.debug(f"app.get.sse: Request received: {method} {url} from {client_ip}")
    logger.debug(f"app.get.sse: User-Agent: {user_agent}")
    # I should learn pytest better. I want to test sse messages.
    # return EventSourceResponse(mock_event_generator(request))
    return EventSourceResponse(event_generator(request))

async def event_generator(request: Request):
    message_id_counter = 0
    logger.debug("app.event_generator: Starting SSE event generator.")
    while True:
        if await request.is_disconnected():
            break
        message = await global_message_queue.get()
        try:
            event = message['event']
            data = message['data']
            logger.debug(f"app.event_generator: Message received from the queue. Event: {event}, Data: {data}")
            # Just in case the message is an empty string or None.
            if message:
                message_id_counter += 1
                yield {
                    "event": event,
                    "id": str(message_id_counter),
                    "retry": RETRY_TIMEOUT,
                    "data": data
                }
        except:
            logger.error(f"app.event_generator: Error sending message: {message}")


@app.get("/api/v1/health")
async def health_check():
    logger.debug("app.health_check: Health check endpoint accessed.")
    return {"status": "ok"}


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)