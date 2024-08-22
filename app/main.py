import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.dependencies import get_queue_manager
from app.routes import audio_processing, sse, health
from app.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup")
    # Ensure the audio directory exists
    os.makedirs("audio", exist_ok=True)

    # Initialize a task variable to handle asyncio.cancel() calls
    global task
    task = None

    # Initialize queue manager
    queue_manager = await get_queue_manager()
    await queue_manager.initialize()

    yield # Run the application

    # Shutdown
    logger.info("Application shutdown")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("Background task cancelled during shutdown")

    # Cleanup queue manager
    await queue_manager.cleanup()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

app.include_router(audio_processing.router, prefix="/api/v1", tags=["audio"])
app.include_router(sse.router, prefix="/api/v1", tags=["sse"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
