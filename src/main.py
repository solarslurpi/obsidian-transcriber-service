'''I was going crazy trying to truly understand sse traffic and how it is implemented through FastAPI, EventStore (javascript), using TestClient(app), using AsyncClient(app)... there was alot.  At one point i put my head down and wrote this to help figure it out.  This server side helped me test stuff out.'''
import asyncio
import logging

from fastapi import FastAPI, Request
from sse_starlette import EventSourceResponse
from dotenv import load_dotenv
load_dotenv()
from global_stuff import global_message_queue
from logger_code import LoggerBase

app = FastAPI()

logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)

@app.get("/")
async def root():
    return {"message": "Tomato"}

async def send_messages():
    logger.debug("send_messages: Starting to send messages.")
    for i in range(40):
        await asyncio.sleep(2)  # Simulate delay between messages
        await global_message_queue.put(f"Message {i}")
        logger.debug(f"send_messages: Sent Message {i}")


@app.get("/api/v1/sse")
async def sse_endpoint(request: Request):
    logger.debug("app.get.sse: Starting the SSE request. Starting to send messages to the queue.")
    # asyncio.create_task(send_messages())
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get('user-agent', 'unknown')

    logger.debug(f"app.get.sse: Request received: {method} {url} from {client_ip}")
    logger.debug(f"app.get.sse: User-Agent: {user_agent}")
    # asyncio.create_task(send_messages())
    return EventSourceResponse(event_generator(request))

async def event_generator(request: Request):
    logger.debug("event_generator: Starting the event generator.")
    while True:
        yield {
            "event": "message",
            "id": "1",
            "retry": 10000,
            "data": "some data\n\n"
        }
        logger.debug("sent.")
        await asyncio.sleep(3)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(f"{__name__}:app", host="127.0.0.1", port=8000, reload=True)