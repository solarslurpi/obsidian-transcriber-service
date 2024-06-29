import asyncio
import logging
import os
import time
from dotenv import load_dotenv
load_dotenv()

from transcription_code import TranscribeAudio
from exceptions_code import   LocalFileException, MetadataExtractionException, TranscriptionException, SendSSEDataException
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

        # If all the properties of the state are cached, we can send the all fields the client needs.
        if state.is_complete(): # This means the state is already in the cache.
            await send_sse_data_messages(state, ["key","basename","num_chapters","metadata","chapters"])
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
        await send_sse_message("status", "Have the content.  Need a few moments to process.  Please hang on.")
        # Ordered the num_chapters early on because keeping track of the number of chapters. This way the client can better keep track of incoming chapters.
        await send_sse_data_messages(state,["key","num_chapters","basename","metadata","chapters"])

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


async def send_sse_data_messages(state, content_texts: list):
    '''The data messages:
    1. key
    2. basename
    3. num_chapters
    4. metadata
    5. chapters
    key, basename, num_chapters are simple strings.  metadata is a dictionary. Chapters is a list of chapters, each chapter contains the start_time, end_time, and transcript text. A small delay is added between each message to allow the client to process the data and let the server process other tasks.'''
    for content_text_property in content_texts:
        try:
            if content_text_property == "metadata":
                await send_sse_message("data", {'metadata': state.metadata.model_dump(mode='json')})
            elif content_text_property == "chapters":
                for chapter in state.chapters:
                    await send_sse_message("data", {'chapter': chapter.model_dump()})
                    await asyncio.sleep(0.1)
            elif content_text_property == "num_chapters":
                value = len(state.chapters)
                await send_sse_message("data", {content_text_property:value})
            else:
                value = getattr(state, content_text_property)
                await send_sse_message("data", {content_text_property:value})
            await asyncio.sleep(0.1)
        except SendSSEDataException as e:
            logger.error(f"process_check_code.send_sse_data_messages: Error {e}.")
            raise e
