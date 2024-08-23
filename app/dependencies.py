from fastapi import Request
from app.service.message_queue_manager import MessageQueueManager

async def get_message_queue_manager(request: Request) -> MessageQueueManager:
    if not hasattr(request.app.state, "queue_manager"):
        request.app.state.message_queue_manager = MessageQueueManager()
    return request.app.state.message_queue_manager
