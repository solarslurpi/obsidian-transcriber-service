import asyncio
import logging
import os

from fastapi import APIRouter, Request, Depends, File, Form, UploadFile, HTTPException
from typing import Optional

import app.logging_config

from app.service.message_queue_manager import initialize_message_queue_manager
from app.service.utils import send_sse_message, get_audio_directory
from app.service.audio_processing_model import AudioProcessRequest
from app.service.process_audio import process_audio
# from app.services.audio_processor import process_audio

router = APIRouter()

logger = logging.getLogger(__name__)

# Global lock for processing
processing_lock = asyncio.Lock()

@router.post("/process_audio")
async def init_process_audio(request: Request,
                             youtube_url: Optional[str] = Form(None),
                             upload_file: UploadFile = File(None),
                             audio_quality: str = Form("default"),
                             compute_type: str = Form("int8"),
                             chapter_chunk_time: int = Form(10)):

    if processing_lock.locked():
        raise HTTPException(status_code=409, detail="Another process is already running")

    async with processing_lock:
        return await init_process_audio(
            youtube_url=youtube_url,
            upload_file=upload_file,
            audio_quality=audio_quality,
            compute_type=compute_type,
            chapter_chunk_time=chapter_chunk_time,
            request = request,
        )

async def init_process_audio(
    youtube_url: Optional[str],
    upload_file: UploadFile,
    audio_quality: str,
    compute_type: str,
    chapter_chunk_time: int,
    request: Request
):
    try:
        # THIS IS THE STARTUP - PROBABLY QUEUE MAYBE STATE??? MAYBE STATES on app.state????
        # The message queue needs to be refreshed each time we process a new audio file.
        request.app.state.message_queue_manager = await initialize_message_queue_manager()
        queue_manager = request.app.state.message_queue_manager
        await send_sse_message(queue_manager,"status", "Received audio processing request.")
        # Instantiante and trigger Pydantic class validation.
        audio_input = AudioProcessRequest(
            youtube_url=youtube_url,
            audio_filename=upload_file.filename if upload_file else None,
            audio_quality=audio_quality,
            compute_type = compute_type,
            chapter_chunk_time = chapter_chunk_time
        )
        logger.info(f"Audio input: youtube_url: {audio_input.youtube_url}, audio_filename: {audio_input.audio_filename}, audio_quality: {audio_input.audio_quality}, compute_type: {audio_input.compute_type}, chapter_chunk_time: {audio_input.chapter_chunk_time}")
    except ValueError as e:
        await send_sse_message(queue_manager,"server-error", str(e))
        return {"status": f"Error reading in the audio input. Error: {e}"}
    if upload_file:
        # Save the audio file locally to use for transcription processing.
        try:
            save_local_audio_file(upload_file)
        except OSError as e:
            error_message = f"OS error occurred while saving uploaded audio file: {e}"
            await send_sse_message(queue_manager,"server-error", error_message)
            return {"status": error_message}
        except Exception as e:
            error_message = f"Unexpected error occurred while saving uploaded audio file: {e}"
            await send_sse_message(queue_manager, "server-error", error_message)
            return {"status": error_message}
    request.app.state.task = asyncio.create_task(process_audio(queue_manager, audio_input))
    logger.debug("in init_process_audio. returning status.")
    return {"status": "Transcription process has started."}

def save_local_audio_file(upload_file: UploadFile):
    try:
        audio_directory = get_audio_directory()
        file_location = os.path.join(audio_directory, upload_file.filename)
        if not os.path.exists(file_location):
            with open(file_location, "wb+") as file_object:
                file_object.write(upload_file.file.read())
            logger.debug(f"File saved to {file_location}")
        else:
            logger.debug(f"File {file_location} already exists.")
        return file_location
    except OSError as e:
        logger.error(f"Failed to save file {upload_file.filename} due to OS error: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving file {upload_file.filename}: {e}")
        raise
