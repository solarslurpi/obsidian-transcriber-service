#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###########################################################################################
# Author: Margaret Johnson
# Copyright (c) 2024 Margaret Johnson
###########################################################################################
import asyncio
import logging
import time
from typing import List

import app.logging_config
from pydantic import BaseModel, field_validator
from app.service.audio_processing_model import AudioProcessRequest
from app.service.message_queue_manager import MessageQueueManager
from app.service.transcription_code import TranscribeAudio
from app.service.transcription_state_code import TranscriptionState, TranscriptionStatesSingleton, initialize_transcription_state
from app.service.exceptions_code import   LocalFileException, MetadataExtractionException, TranscriptionException, SendSSEDataException
from app.service.utils import send_sse_message, format_time

# Create a logger instance for this module
logger = logging.getLogger(__name__)


async def process_audio(queue: MessageQueueManager, audio_input: AudioProcessRequest):
    # State data client requires:
    # filename, num_chapters, frontmatter, chapters (sent a chapter at a time, includes the transcript)/
    # Status messages sent "liberally" to let the client know what's going on.
    await send_sse_message(queue, "status", "We're on it! Checking inventory...")
    # Fill up as much of the state as possible.
    state = None # Once instantiated, it is a TranscriptionState instance.
    try:
        logger.info("Initializing transcription state.")
        state, local_audio_filename = await initialize_transcription_state(queue, audio_input)

        # If all the properties of the state are cached, we can send the all fields the client needs.
        if state.is_complete(): # This means the transcript text is already in the state instance.
            logger.info("State is complete. Sending content to the client.")
            await send_sse_data_messages(queue, state, ["key","basename","num_chapters","metadata","chapters"])
            return
    except asyncio.CancelledError as e:
        logger.debug("Transcription cancelled.")
        if state:
            state = None
        await send_sse_message(queue,"server-error", "Transcription cancelled.")
        return

    except MetadataExtractionException as e:
        await send_sse_message(queue, "server-error", "Error extracting metadata.")
        logger.error(f"Error extracting metadata",exc_info=e)
        # iF the metadata can't be read, there is no state to save.
        return
    except LocalFileException as e:
        await send_sse_message(queue, "server-error", "Error saving uploaded mp3 file.")
        # The uploaded mp3 file isn't saved, so there is no state to save.
        if state:
            state = None
        logger.error(f"Error saving uploaded mp3 file",exc_info=e)
        return
    except Exception as e:
        await send_sse_message(queue, "server-error", str(e))
        logger.error(f"An unexpected error occurred",exc_info=e)

        # This is an unexpected error, so not sure the state is valid.
        if state:
            state = None
        return


    transcribe_audio_instance = TranscribeAudio(audio_input.audio_quality, audio_input.compute_type, audio_input.chapter_chunk_time)

    try:
        start_time = time.time()
        # The chapters currently have th start/stop metadata but not chapter num and not chapter text.
        state.chapters = await transcribe_audio_instance.transcribe(queue, local_audio_filename,state.chapters)
        end_time = time.time()
        state.metadata.transcription_time = format_time(float(end_time - start_time))
    except asyncio.CancelledError as e:
        logger.debug("Transcription cancelled.")
        await send_sse_message(queue, "server-error", "Transcription cancelled.")
        if state:
            state = None
        return

    except TranscriptionException as e:
        await send_sse_message(queue, "server-error", f"Error during transcription {e}")
        logger.error(f"Error during transcription",exc_info=e)
        # Keep the state in case the client wants to try again.
        raise

    except Exception as e:
        await send_sse_message(queue, "server-error", f"An unexpected error occurred: {e}")
        logger.error(f"An unexpected error occurred",exc_info=e)
        # This is an unexpected error, so not sure the state is valid.
        if state:
            state = None
        raise
    # The state is now complete.  Add the transcript text to the cache.
    states = TranscriptionStatesSingleton().get_states()
    states.add_state(state)
    logging.debug(f"Transcription complete.  Transcription time: {state.metadata.transcription_time}.  Final State added to cache.")

    await send_sse_message(queue , "status", "Have the content.  Need a few moments to process.  Please hang on.")
    # Ordered the num_chapters early on. This way the client can better keep track of incoming chapters.
    await send_sse_data_messages(queue, state,["key","num_chapters","basename","metadata","chapters"])

class ContentTextsModel(BaseModel):
    content_texts: List[str]

    @field_validator('content_texts')
    def validate_content_texts(cls, v):
        expected_set = {"key", "basename", "num_chapters", "metadata", "chapters"}
        for item in v:
            if item not in expected_set:
                raise ValueError(f"Invalid content text: {item}")
        return v

async def send_sse_data_messages(queue: MessageQueueManager, state:TranscriptionState, content_texts: List):
    '''The data messages:
    1. key
    2. basename
    3. num_chapters
    4. metadata
    5. chapters
    key, basename, num_chapters are simple strings.  metadata is a dictionary. Chapters is a list of chapters, each chapter contains the start_time, end_time, and transcript text. A small delay is added between each message to allow the client to process the data and let the
    server process other tasks.'''
    try:
        # Validate content_texts
        ContentTextsModel(content_texts=content_texts)
    except ValueError as e:
        errors = e.errors()
        invalid_values = [str(error['input']) for error in errors if 'input' in error]
        logger.error(f"Number of validation errors: {len(errors)}.  Invalid values: {invalid_values}")

        await send_sse_message(queue, "status", f"Invalid values: {invalid_values}")
        return
    # Hold off to let the status messages go through.
    await asyncio.sleep(2)
    # Reset the state
    await send_sse_message(queue, "reset-state", "Clear out the previous content.")
    logger.debug('sent reset-state')
    await asyncio.sleep(2)
    for content_text_property in content_texts:
        try:
            if content_text_property == "metadata":
                l = state.metadata.model_dump(mode='json')
                await send_sse_message(queue, "data", {'metadata': state.metadata.model_dump(mode='json')})
                logger.debug('sent metadata')
            elif content_text_property == "chapters":

                for chapter in state.chapters:
                    await send_sse_message(queue, "data", {'chapter': chapter.to_dict_with_start_end_strings()})
                    # Add a delay to allow the service to process the data as well as allow the client to have time to process the data.
                    # I used 2 seconds.  This is a bit arbitrary.  It could be adjusted.
                    logger.debug(f'sent chapter {chapter.number} ')
                    await asyncio.sleep(2)
            elif content_text_property == "num_chapters":
                value = len(state.chapters)
                await send_sse_message(queue, "data", {content_text_property:value})
                logger.debug(f'sent num_chapters {value}')
            else:
                value = getattr(state, content_text_property)
                await send_sse_message(queue, "data", {content_text_property:value})
                logger.debug(f'sent {content_text_property} {value}')
            # Add a delay to allow the service to process the data as well as allow the client to have time to process the data.
            # I used 2 seconds.  This is a bit arbitrary.  It could be adjusted.
            await asyncio.sleep(2)
        except SendSSEDataException as e:
            logger.error(f"process_check_code.send_sse_data_messages: Error {e}.")
            raise e
    logger.info(f'***Content: {", ".join(content_texts)} sent***')