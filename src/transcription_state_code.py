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
import json
import logging
import os
import time
from typing import Optional, List, Tuple, Dict, Union


from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer

import logging_config
from exceptions_code import KeyException, MetadataExtractionException
from metadata_extractor_code import MetadataExtractor
from metadata_shared_code import Metadata, build_metadata_instance
from audio_processing_model import AudioProcessRequest
from utils import send_sse_message, format_time


# Create a logger instance for this module
logger = logging.getLogger(__name__)

from typing import Dict,List, Optional
from pydantic import BaseModel, Field

class Chapter(BaseModel):
    title: Optional[str] = Field(default='', description="Title of the chapter.")
    start_time: float = Field(..., description="Start time of the chapter in seconds.")
    end_time: float = Field(..., description="End time of the chapter in seconds.")
    text: Optional[str] = Field(default=None, description="Transcription of the chapter.")
    number: Optional[int] = Field(default=None, description="Chapter number.")

    def to_dict_with_start_end_strings(self) -> dict:
        '''Used to return a dictionary with straing formated start and end times.'''
        return {
            "title": self.title,
            "start_time": format_time(self.start_time),
            "end_time": format_time(self.end_time),
            "text": self.text,
            "number": self.number
        }

def build_chapters(chapter_dicts: List[Dict]) -> List[Chapter]:
    chapters = []
    try:
        for chapter_dict in chapter_dicts:
            # At this point the chapter_dict contains the title, start_time, and end_time. The transcript is added later.
            chapter = Chapter(**chapter_dict)
            chapters.append(chapter)
    except Exception as e:
        raise e
    return chapters

class TranscriptionState(BaseModel):
    # Manages the state and behavior of a single transcription.
    key: str = Field(..., description="A unique key that allows the client to request the same content again by querying the state with this key.")
    basename: str = Field(..., description="Basename of the transcript note to be used by the client when creating the note.")
    local_audio_path: str = Field(..., description="Local storage of the audio file. ")
    metadata: Metadata = Field(default=None, description="Turned into YAML frontmatter for a (Obsidian) note. YouTube metadata is very rich.  audio files not so much...")
    chapters: List[Chapter] = Field(default_factory=list, description="Each entry provides the metadata as well as the transcript text of a chapter of audio content.")

    @field_validator('chapters')
    def check_chapters(cls, v):
        if len(v) == 1:
            v[0].end_time = 0.0
        return v

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def update_chapter(self, start: int, transcription: str) -> None:
        for chapter in self.chapters:
            if chapter.start_time == start:
                chapter.text = transcription
                break
        else:
            raise ValueError(f"No chapter found with start time {start}")

    def clear_chapters(self) -> None:
        self.chapters = []

    def is_complete(self) -> bool:
        # Check if all required fields are set.
        required_fields = ['key', 'basename', 'local_audio_path', 'metadata', 'chapters']
        for field in required_fields:
            try:
                if getattr(self, field) is None: # field exists and is None
                    return False
            except AttributeError as e: # field does not exist
                logger.error(f"{field} does not exist.", exc_info=e)
                raise
        # Check if there is at least one chapter
        if len(self.chapters) == 0:
            return False
        # Additionally, check that each chapter has transcription_text filled out
        for chapter in self.chapters:
            if not chapter.text:
                return False
        return True

    def cleanup(self) -> None:
        """Cleanup resources held by the TranscriptionState."""
        # Clear chapters
        self.clear_chapters()
        # Nullify other fields
        self.local_audio_path = None
        self.key = None
        self.metadata = None
        self.transcript_done = False


class TranscriptionStates:
    # Manages a collection of multiple TranscriptionState instances.
    def __init__(self):
        self.cache = {}
        self.state_file = 'state_cache/state_cache.json'

    def add_state(self, transcription_state: TranscriptionState):
        '''This method stres an instance of the transcription_state in the cache dictionary with the specified key, making it available for retrieval during subsequent requests, assuming the application's state is preserved between those requests.'''
        if not isinstance(transcription_state, TranscriptionState):
            raise ValueError("transcription_state must be an instance of TranscriptionState.")
        self.cache[transcription_state.key] = transcription_state
        self.save_state(transcription_state)


    def save_state(self, state):
        '''This method saves the transcription_state to a file with the specified key as the filename.'''
        states_dict = {}
        try:
            with open(self.state_file, 'r') as file:
                states_dict = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            states_dict = {}

        except Exception as e:
            return
        # The state has been validated.
        states_dict[state.key] = state.model_dump()
        # Save the model to a JSON file
        with open(self.state_file, 'w') as file:
            json.dump(states_dict, file, indent=2)


    def load_states(self):
        '''Open state_cache.json and load any of the stored state dictionaries into the cache.'''
        state_loaded = False
        try:
            with open(self.state_file, 'r') as file:
                data = json.load(file)
            for key, value in data.items():
                try:
                    # Create TranscriptionState object from the loaded data
                    state = TranscriptionState(**value)
                    # Verify the audio file is available locally for transcription. If it isn't available, skip this state.
                    if not os.path.exists(state.local_audio_path):
                        continue
                    self.cache[key] = state
                    state_loaded = True
                except (TypeError, KeyError, ValueError) as e:
                    continue
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return state_loaded
        return state_loaded


    def get_state(self, key: str) -> Optional[TranscriptionState]:
        return self.cache.get(key)

    def make_key(self, audio_input: AudioProcessRequest) -> str:
        if audio_input.youtube_url:
            name_part = audio_input.youtube_url
        elif audio_input.audio_filepath:
            name_part = os.path.basename(audio_input.audio_filepath)
        else: # Given both the youtube URL are None and the audio_file is None, the code doesn't have an audio file to transcribe.
            raise KeyException("No youtube url or audio file to transcribe.")
        key = name_part + "_" + audio_input.audio_quality + "_" + audio_input.compute_type + "_" + str(audio_input.chapter_time_chunk)
        return key

class TranscriptionStatesSingleton:
    '''To maintain the states across requests.'''
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TranscriptionStatesSingleton, cls).__new__(cls, *args, **kwargs)
            cls._instance.states = TranscriptionStates()
        return cls._instance

    @classmethod
    def get_states(cls,load_from_store:bool=True):
        if cls._instance is None:
            cls._instance = cls()
        if load_from_store:
            cls._instance.states.load_states()
        return cls._instance.states

async def initialize_transcription_state(audio_input: AudioProcessRequest) -> Tuple[TranscriptionState, Metadata]:
    logger.debug(f"audio_input: {audio_input}")
    try:
        states = TranscriptionStatesSingleton().get_states()
        key = states.make_key(audio_input)
    except KeyException as e:
        await send_sse_message(f"server-error", str(e))
        logger.error(f"KeyException error",exc_info=e)
        if state:
            state = None
        return

    state = states.get_state(key)
    # END COMMENTING OUT FOR TESTS.
    # maintain the key for the client in case content is missing.

    logger.debug(f"state key is: {key}")
    if state:
        logger.debug("state is in the cache.")
        await send_sse_message("status", "Sheer happiness! We already have the content.")
        return state
    else:
        await send_sse_message(event="status", data="Setting up stuff, back shortly!")
        logger.debug("state is not in the cache. Retrieving content.")
        extractor = MetadataExtractor()
        try:
            start_time = time.time()
            info_dict, chapter_dicts, audio_filepath = await extractor.extract_metadata_and_chapter_dicts(audio_input)
            end_time = time.time()


        except MetadataExtractionException as e:
            raise e
        except Exception as e:
            raise


    # At this point, we have everything except the transcript_text of the chapters.
    try:
        # Build the state
        metadata = build_metadata_instance(info_dict)
        metadata.download_time = format_time(float(end_time - start_time))
        metadata.audio_input = audio_input

        chapters = build_chapters(chapter_dicts)
        filename_no_extension = os.path.splitext(os.path.basename(audio_filepath))[0]
        state = TranscriptionState(key=key, basename=filename_no_extension, local_audio_path=audio_filepath, hf_model=audio_input.audio_quality,  metadata=metadata, chapters=chapters)
        # Since we are here, add the first process of audio prep prior to transcription to the cache
        states.add_state(state)
        await send_sse_message(event="status", data="Content has been prepped. All systems go for transcription.")
    except Exception as e:
        logger.error(f"Error building state",exc_info=e)
        await send_sse_message(event="server-error", data=f"Error building state: {e}")
        raise e
    state.key = key
    return state
