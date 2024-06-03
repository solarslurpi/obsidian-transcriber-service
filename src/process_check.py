# Example usage in process_check
import asyncio
import logging
import os

from logger_code import LoggerBase
from transcription_code import TranscribeAudio
from transcription_state_code import initialize_transcription_state, TranscriptionState
from youtube_download_code import YouTubeDownloader

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

async def process_check(audio_input):
    logger.debug(f"process_check_code.process_check: audio_input: {audio_input}")
    # Fill up as much of the state as possible.
    state = initialize_transcription_state(audio_input)
    logger.debug("process_check_code.process_check: state initialized.")
    transcribe_audio_instance = TranscribeAudio()
    # If the mp3 file is readily available, transcribe it.
    if state is not None and state.local_mp3:
        logger.debug("process_check_code.process_check: state is local_mp3. Off to transcription.")

        asyncio.create_task(transcribe_audio_instance.transcribe_chapters(state, logger))
    else:
        # If it is a youtube video, download first.
        download_instance = YouTubeDownloader(state.youtube_url, logger)
        logger.debug("process_check_code.process_check: state is youtube_url. Off to download YouTube video.")
        # TODO filename for the youtube download mp3.
        filename = f'{LOCAL_DIRECTORY}/' + state.metadata.get('filename', 'youtube_audio')
        # The all important local_mp3 name can now be set.
        state.local_mp3 = f"{filename}.mp3"
        asyncio.create_task(download_instance.download_audio(state.youtube_url, filename))
        # Wait until the local_mp3 file is available before transcription can begin.
        await asyncio.create_task(transcribe_audio_instance.transcribe_chapters(state, logger) )
