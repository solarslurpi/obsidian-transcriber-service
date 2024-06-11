# Example usage in process_check
import asyncio
import logging
import os
from dotenv import load_dotenv
load_dotenv()

from transcription_code import TranscribeAudio
from exceptions_code import handle_exception, LocalFileException, MetadataExtractionException, TranscriptionException
from logger_code import LoggerBase
from transcription_state_code import initialize_transcription_state
from youtube_download_code import youtube_download, sanitize_title


LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

async def process_check(audio_input):
    logger.debug(f"process_check_code.process_check: audio_input: {audio_input}")
    # Fill up as much of the state as possible.
    state = None # Once instantiated, it is a TranscriptionState instance.
    try:
        state = await initialize_transcription_state(audio_input)
        logger.debug("process_check_code.process_check: state initialized.")

    except MetadataExtractionException as e:
        await handle_exception(e, 500, "Error extracting metadata.", logger)
        # iF the metadata can't be read, there is no state to save.
        return
    except LocalFileException as e:
        await handle_exception(e, 500, "Error saving uploaded mp3 file. ", logger)
        # The uploaded mp3 file isn't saved, so there is no state to save.
        if state:
            state = None
        return
    except Exception as e:
        await handle_exception(e, 500, "An unexpected error occurred.",logger)
        # This is an unexpected error, so not sure the state is valid.
        if state:
            state = None
        return

    transcribe_audio_instance = TranscribeAudio()
    # If the mp3 file is readily available, transcribe it.
    if state is not None and state.local_mp3:
        logger.debug("process_check_code.process_check: state is local_mp3. Off to transcription.")

        asyncio.create_task(transcribe_audio_instance.transcribe_chapters(state))
    else:
        # If it is a youtube video, download first.
        logger.debug("process_check_code.process_check: state is youtube_url. Off to download YouTube video.")
        # In the case of a youtube video, the local mp3 filename is based on the youtube title.
        state.local_mp3 = f'{LOCAL_DIRECTORY}/' + sanitize_title(state.metadata.title) + ".mp3"

        youtube_download(youtube_url=audio_input.youtube_url, base_filename=state.local_mp3)
        "Each chapter is represented as a coroutine, allowing for concurrent processing. The code waits for all these coroutines to complete execution."
        try:
            await transcribe_audio_instance.transcribe_chapters(state)
        except TranscriptionException as e:
            await handle_exception(e, 500, "Error during transcription.", logger)
            # Keep the state in case the client wants to try again.
            return

        except Exception as e:
            await handle_exception(e, 500, "An unexpected error occurred.",logger)
            # This is an unexpected error, so not sure the state is valid.
            if state:
                state = None
            return