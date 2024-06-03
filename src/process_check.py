# Example usage in process_check
import asyncio
import logging
from logger_code import LoggerBase
from transcription_code import TranscribeAudio
from transcription_state_code import initialize_transcription_state
from youtube_download_code import YouTubeDownloader

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

async def process_check(audio_input):
    logger.debug(f"process_check_code.process_check: audio_input: {audio_input}")
    # Fill up as much of the state as possible.
    state = initialize_transcription_state(audio_input)
    logger.debug("process_check_code.process_check: state initialized.")
    transcribe_audio_instance = TranscribeAudio()
    # If the mp3 file is readily available, transcribe it.
    if state.local_mp3:
        logger.debug("process_check_code.process_check: state is local_mp3. Off to transcription.")

        asyncio.create_task(transcribe_audio_instance.transcribe_chapters(state, logger))
    else:
        # If it is a youtube video, download first.
        download_instance = YouTubeDownloader(state.youtube_url, logger)
        logger.debug("process_check_code.process_check: state is youtube_url. Off to download YouTube video.")
        asyncio.create_task(download_instance.download_audio, state, logger)
        # Wait until the local_mp3 file is available before transcription can begin.
        await asyncio.create_task(transcribe_audio_instance.transcribe_chapters, state, logger)
