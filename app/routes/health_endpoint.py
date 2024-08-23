from fastapi import APIRouter
from fastapi import Request
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check(request: Request):
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get('user-agent', 'unknown')

    logger.debug(f"app.health_check: Health check endpoint accessed. Request received: {method} {url} from {client_ip}")
    logger.debug(f"app.health_check: User-Agent: {user_agent}")

    return {"status": "ok"}