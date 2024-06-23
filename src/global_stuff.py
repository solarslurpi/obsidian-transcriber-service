import asyncio

# Queue to communicate betwen threads so that SSE messages can be sent asynchronously.
global_message_queue = asyncio.Queue()
