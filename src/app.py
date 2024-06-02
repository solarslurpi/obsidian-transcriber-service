import asyncio
import logging
from fastapi import FastAPI, Depends, Request
from sse_starlette import EventSourceResponse
from global_stuff import global_message_queue
from logger_code import LoggerBase
from router_code import router
from pydantic_models import AudioProcessRequest, as_form

app = FastAPI()
# Set up logging filte
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

logger_one = logging.getLogger('router_code')
logger_one.setLevel(logging.DEBUG)

@app.post("/api/v1/process_audio")
async def init_process_audio(audio_input: AudioProcessRequest = Depends(as_form)):
    logger.debug(f"app.init_process_audio: audio_input: {audio_input}")
    # Determine if a transcript already exists, whether it is a YouTube URL or an mp3 file.
    # Then go from there.
    asyncio.create_task(router(audio_input))
    return {"status": "Processing audio file."}

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

    while True:
        if await request.is_disconnected():
            break
        message = await global_message_queue.get()
        # Just in case the message is an empty string or None.
        if message:
            logger.debug(f"app.event_generator: Message: **{message}**")
            yield f"{message}\n\n"

@app.get("/api/v1/health")
async def health_check():
    logger.debug("app.health_check: Health check endpoint accessed.")
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
