import asyncio
import logging

from fastapi import APIRouter, Request, HTTPException

from app.service.message_queue_manager import MessageQueueManager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/cancel")
async def cancel_task(
    request: Request
):
    method = request.method
    url = str(request.url)
    logger.debug(f"app.get.cancel_task: Request received: {method} {url}")
    try:
        message_queue = request.app.state.message_queue_manager
        task = request.app.state.task
        await cleanup_task(task, message_queue)

        # Raise the cancellation error to be caught by the except block
        raise asyncio.CancelledError("Task cancelled by user request.")
    except asyncio.CancelledError as e:
        logger.debug(f"Task cancelled: {str(e)}")
        raise HTTPException(status_code=200, detail="Task cancelled successfully.")
    except Exception as e:
        logger.error(f"Error during task cancellation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def cleanup_task(task: asyncio.Task, queue: MessageQueueManager):
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("Task was cancelled successfully")
        finally:
            await queue.cleanup()
            logger.info("Task and queue cleaned up")