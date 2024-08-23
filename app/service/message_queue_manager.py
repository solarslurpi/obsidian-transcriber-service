import asyncio
from asyncio import Queue
import logging

logger = logging.getLogger(__name__)

class MessageQueueManager:
    def __init__(self):
        self.queue = None

    async def initialize(self):
        self.queue = Queue()
        logger.info("MessageQueueManager initialized")

    async def cleanup(self):
        self.queue = None
        logger.info("MessageQueueManager cleaned up")

    async def add_message(self, message):
        if self.queue is None:
            raise ValueError("Queue not initialized")
        await self.queue.put(message)

    async def get_message(self):
        if self.queue is None:
            raise ValueError("Queue not initialized")
        return await self.queue.get()

    def queue_empty(self):
        if self.queue is None:
            raise ValueError("Queue not initialized")
        return self.queue.empty()

async def initialize_message_queue_manager():
    queue_manager = MessageQueueManager()
    await queue_manager.initialize()
    return queue_manager