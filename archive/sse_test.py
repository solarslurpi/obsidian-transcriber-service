"""
The goal of these tests is to ensure the robustness of the client when handling SSE messages.
We aim to verify the client's behavior under various conditions, such as receiving messages out of order or missing some messages.
By simulating these scenarios, we can enhance the client's ability to handle unexpected server responses effectively, ensuring a more reliable and resilient user experience.
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from app import app  # Adjust the import to your actual app module

from global_stuff import global_message_queue

# Constants
RETRY_TIMEOUT = 3000

# Mock event generator function to simulate SSE events
async def mock_event_generator(request: Request):
    messages_to_send = []
    message_id_counter = 0
    while True:
        # Check if the client has disconnected
        if await request.is_disconnected():
            break

        # Simulate getting a message from the global message queue
        message = await global_message_queue.get()

        # Handle 'data' events by collecting and reversing messages
        if message['event'] == 'data':
            messages_to_send.append(message)
            if sum(1 for msg in messages_to_send if msg['event'] == 'data') >= 2:
                messages_to_send.reverse()
                for msg in messages_to_send:
                    message_id_counter += 1
                    yield {
                        "event": msg['event'],
                        "id": str(message_id_counter),
                        "retry": RETRY_TIMEOUT,
                        "data": msg['data']
                    }
                messages_to_send.clear()
        else:
            # Handle non-'data' events immediately
            message_id_counter += 1
            yield {
                "event": message['event'],
                "id": str(message_id_counter),
                "retry": RETRY_TIMEOUT,
                "data": message['data']
            }

# Test the mock event generator using pytest
@pytest.mark.asyncio
async def test_mock_event_generator(mocker: MockerFixture):
    # Step 1: Mock the Request object
    # This simulates the HTTP request received by the FastAPI application
    mock_request = mocker.AsyncMock(spec=Request)
    mock_request.is_disconnected = mocker.AsyncMock(return_value=False)

    # Step 2: Patch the event generator in the app module
    # This replaces the real event generator with our mock_event_generator
    mocker.patch('app.event_generator', new=mock_event_generator)

    # Step 3: Create a test client for the FastAPI application
    # This allows us to make requests to the app as if it were running in production
    client = TestClient(app)

    # Step 4: Make a GET request to the SSE endpoint and stream the response
    with client.stream("GET", "/sse-endpoint") as response:
        events = []
        for event in response.iter_lines():
            events.append(event)
            if len(events) >= 3:
                break

    # Step 5: Verify that the correct number of events were received
    assert len(events) == 3
    assert "first message" in events[0]
    assert "second message" in events[1]
    assert "third message" in events[2]

# Example endpoint definitions for the FastAPI application

# SSE endpoint definition
@app.get("/sse-endpoint")
async def sse_endpoint(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            yield {
                "event": "data",
                "data": "some data"
            }
    return EventSourceResponse(event_generator())

# Example POST endpoint definition
@app.post("/post-endpoint")
async def post_endpoint(request: Request):
    data = await request.json()
    # Process the data received in the POST request
    return JSONResponse(content={"message": "Data received", "data": data})

# Test for the POST request
def test_post_request():
    client = TestClient(app)
    response = client.post("/post-endpoint", json={"key": "value"})
    assert response.status_code == 200
    assert response.json() == {"message": "Data received", "data": {"key": "value"}}
