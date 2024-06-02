import asyncio
from fastapi import HTTPException

from global_stuff import global_message_queue
from metadata_code import MetadataService
from pydantic_models import AudioProcessRequest, global_state
from transcription_cache_code import TranscriptionCache
async def process_check(audio_input, logger):
    logger.debug(f"process_check_code.process_check: audio_input: {audio_input}")
    if have_local_mp3_and_chapters(audio_input):
    # Check if audio input is in the global_transcription_cache.
    # We need our cache key.  \
    # cache_key = (audio_input.youtube_url or audio_input.file.filename) + '-' + audio_input.audio_quality
    metadata_service = MetadataService()
    if is_youtube_url(audio_input):
        cache_key = audio_input.youtube_url+'-'+audio_input.audio_quality
        logger.debug(f"process_check_code.process_check: cache_key: {cache_key}")
        # Keep updating the global_state when new info comes in.
        global_state.update(youtube_url=audio_input.youtube_url, audio_quality=audio_input.audio_quality)
        # metadata service puts the metadata into global_state.
        metadata_service.extract_youtube_metadata(audio_input.youtube_url, logger)
        logger.debug("Extracted metadata from YouTube video.")
    else:
        cache_key = audio_input.file.filename+'-'+audio_input.audio_quality
        # We need to get the mp3 file from the UploadFile object to an mp3 file with local storage.
        mp3_filepath = f"temp/{audio_input.file.filename}"
        global_state.update(mp3_filepath=mp3_filepath, audio_quality=audio_input.audio_quality)
        metadata_service.extract_mp3_metadata(mp3_filepath, logger)
    # Initialize the transcription cache
    transcription_cache = TranscriptionCache(cache_key)
    logger.debug(f"process_check_code.process_check: transcription_cache is available.  Num chapters with transcripts: {transcription_cache.num_chapters_with_transcripts}.  Total number of chapters: {transcription_cache.num_chapters_total}")
    # Check if there are chapters in the transcription cache.
    if transcription_cache.num_chapters_with_transcripts > 0:
        # If there are chapters in the transcription cache, We want to get the
        # client up to speed with the current state of the transcription.
        asyncio.create_task(update_client_state, transcription_cache)


def is_youtube_url(request: AudioProcessRequest) -> bool:
    if request.youtube_url and request.file:
        raise HTTPException(status_code=400, detail="Please provide either a YouTube URL or an MP3 file, not both.")
    elif request.youtube_url:
        return True
    elif request.file:
        return False
    else:
        raise HTTPException(status_code=400, detail="No YouTube URL or file provided.")

async def update_client_state(transcription_cache):
    # Get the chapters from the transcription cache
    chapters = transcription_cache.get_chapters()
