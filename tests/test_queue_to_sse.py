import asyncio
import pytest
import httpx
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Verify PYTHONPATH is set
print("PYTHONPATH:", os.getenv("PYTHONPATH"))

from app import app  # Ensure this works correctly with the PYTHONPATH set
from global_stuff import global_message_queue
from logger_code import LoggerBase

logger = LoggerBase.setup_logger(__name__)

# Background task to send messages to the global message queue
async def send_messages():
    for i in range(40):
        await asyncio.sleep(2)  # Simulate delay between messages
        await global_message_queue.put(f"Message {i}")
        logger.debug(f"send_messages: Sent Message {i}")

@pytest.mark.asyncio
async def test_sse_endpoint():
    logger.debug("Starting the SSE request")

    # Start the message sender in the background
    await asyncio.create_task(send_messages())

    # async with httpx.AsyncClient(app=app, base_url="http://127.0.0.1:8000") as async_client:
    #     async with async_client.stream("GET", "/api/v1/sse") as response:
    #         assert response.status_code == 200

    #         event_data = ""
    #         async for line in response.aiter_lines():
    #             if line:
    #                 print(f"Line: {line}")
    #                 if line.startswith("event: "):
    #                     event_data = line.replace('event: ', '')
    #                 elif line.startswith("data: "):
    #                     event_data += line.replace('data: ', '')
    #                 print(f"Event data: {event_data}")

    #                 # Check that the first message is the expected message
    #                 assert "Message" in event_data
    #                 break  # Stop after receiving the first message

    logger.debug("Finished processing the SSE events")
