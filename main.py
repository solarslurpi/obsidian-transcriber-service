
import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import app.logging_config
from app.config import settings
from app.service.message_queue_manager import initialize_message_queue_manager
from app.routes import process_audio_endpoint, sse_endpoint, health_endpoint, cancel_endpoint, missing_content_endpoint
from app.routes.cancel_endpoint import cleanup_task

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
     # Startup
     app.state.task = None
     logger.info("Application startup")
     # Ensure the audio directory exists
     os.makedirs("audio", exist_ok=True)


     # The message queue is reinitialized when a post comes in. This call is perhaps redundant. However, it helps to not only ensure the message queue is initially created, but also the app state that is used for this process.
     app.state.message_queue_manager = await initialize_message_queue_manager()

     yield # Run the application

     await cleanup_task(app.state.task, app.state.message_queue_manager)


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# Note: Only one client at a time. See the route.
app.include_router(process_audio_endpoint.router, prefix="/api/v1", tags=["process_audio"])
app.include_router(sse_endpoint.router, prefix="/api/v1", tags=["sse"])
app.include_router(health_endpoint.router, prefix="/api/v1", tags=["health"])
app.include_router(cancel_endpoint.router, prefix="/api/v1", tags=["cancel"])
app.include_router(missing_content_endpoint.router, prefix="/api/v1", tags=["missing_content"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)