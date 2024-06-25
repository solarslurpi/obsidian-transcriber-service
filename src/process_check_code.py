
import logging
import os
import time
from dotenv import load_dotenv
load_dotenv()

from transcription_code import TranscribeAudio
from exceptions_code import   LocalFileException, MetadataExtractionException, TranscriptionException
from logger_code import LoggerBase
from transcription_state_code import initialize_transcription_state
from utils import send_sse_message


LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

async def process_check(audio_input):
    # State data client requires:
    # filename, num_chapters, frontmatter, chapters (sent a chapter at a time, includes the transcript)/
    # Status messages sent "liberally" to let the client know what's going on.
    await send_sse_message("status", "We're on it! Checking inventory...")
    logger.debug(f"process_check_code.process_check: audio_input: {audio_input}")
    # Fill up as much of the state as possible.
    state = None # Once instantiated, it is a TranscriptionState instance.
    try:

        state = await initialize_transcription_state(audio_input)
        logger.debug("process_check_code.process_check: state initialized.")
        # Send basename and num_chapters to the client since these are complete regardless if the state was already cached.
        await send_sse_message("data", {'basename': state.basename})
        await send_sse_message("data", {'num_chapters': len(state.chapters)})
        # If all the properties of the state are cached, we can send the all fields the client needs.
        if state.is_complete():
            await send_sse_message("status", "Lickity split! We already have the content.")
            await send_sse_message("data", {'metadata': state.metadata.model_dump(mode='json')})
            for chapter in state.chapters:
                await send_sse_message("data", {'chapter': chapter.model_dump()})
            await send_sse_message("status", "Finished.  Please come again!")
            return


    except MetadataExtractionException as e:
        await send_sse_message("server-error", "Error extracting metadata.")
        # iF the metadata can't be read, there is no state to save.
        return
    except LocalFileException as e:
        await send_sse_message("server-error", "Error saving uploaded mp3 file.")
        # The uploaded mp3 file isn't saved, so there is no state to save.
        if state:
            state = None
        return
    except Exception as e:
        await send_sse_message("server-error", str(e))

        # This is an unexpected error, so not sure the state is valid.
        if state:
            state = None
        return

    transcribe_audio_instance = TranscribeAudio()

    "Each chapter is represented as a coroutine, allowing for concurrent processing. The code waits for all these coroutines to complete execution."
    try:
        start_time = time.time()
        # The data chapters are sent in transcribe_chapters.
        await transcribe_audio_instance.transcribe_chapters(state)
        end_time = time.time()
        state.metadata.transcription_time = int(end_time - start_time)
        # Finally we have all the metadata info.")
        await send_sse_message("data", {'metadata': state.metadata.model_dump(mode='json')})
        await send_sse_message("status", "Finished.  Please come again!")
    except TranscriptionException as e:
        await send_sse_message("server-error", "Error during transcription.")
        # Keep the state in case the client wants to try again.
        return

    except Exception as e:
        await send_sse_message("server-error", "An unexpected error occurred.")
        # This is an unexpected error, so not sure the state is valid.
        if state:
            state = None
        return