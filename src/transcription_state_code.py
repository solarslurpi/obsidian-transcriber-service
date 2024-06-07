import logging
import os
import torch
from typing import Optional, Dict, List


from pydantic import BaseModel, Field, field_validator


from logger_code import LoggerBase
from metadata_code import MetadataExtractor, ChapterMetadata
from audio_processing_model import AudioProcessRequest, AUDIO_QUALITY_MAP, COMPUTE_TYPE_MAP
from metadata_code import Metadata
from utils import send_message

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class Transcript(BaseModel):
    transcript:str = Field(default=None, description="Transcription of the chapter.")


class TranscriptionState(BaseModel):
    # Manages the state and behavior of a single transcription.
    local_mp3: Optional[str] = Field(default=None, description="Local storage of mp3 file. This is where the transcription part will look for the audio file.")
    hf_model: str = Field(default=None, description="Set when initializing state from user's audio_input.audio_quality.")
    hf_compute_type: torch.dtype = Field(default=None, description="Used by transcriber. Either float32 or float16")
    metadata: Optional[Metadata] = Field(default=None, description="YouTube metadata is very rich.  mp3 file is not so rich in metadata..")
    chapters_transcript: Optional[List[Transcript]] = Field(default_factory=list, description="List of chapters with start and end times and transcriptions.")
    transcription_time: int = Field(default=0,description="Number of seconds it took to transcribe the audio file.")
    transcript_done: bool = Field(default=False, description="True if the transcription is complete.")

    @field_validator('hf_compute_type')
    def check_tensor_dtype(cls, v):
        if v not in [torch.float32, torch.float16]:
            raise ValueError('hf_compute_type must be of type torch.float32 or torch.float16')
        return v

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            torch.dtype: lambda v: str(v).split('.')[-1]
        }

    def add_chapter(self, title: str, start: int, end: int, transcription: Optional[str] = None) -> None:
        self.chapters.append(ChapterMetadata(title=title, start=start, end=end, transcription=transcription))

    def update_chapter(self, start: int, transcription: str) -> None:
        for chapter in self.chapters:
            if chapter.start == start:
                chapter.transcription = transcription
                break
        else:
            raise ValueError(f"No chapter found with start time {start}")

    def clear_chapters(self) -> None:
        self.chapters = []


class TranscriptionStates:
    # Manages a collection of multiple TranscriptionState instances.
    def __init__(self):
        self.cache = {}

    def add_state(self, key: str, transcription_state: TranscriptionState, logger: LoggerBase):
        if not isinstance(transcription_state, TranscriptionState):
            raise ValueError("transcription_state must be an instance of TranscriptionState.")
        self.cache[key] = transcription_state
        logger.debug(f"transcripts_state_code.TranscriptionStates.add_state: {key} added to cache.")

    def get_state(self, key: str) -> Optional[TranscriptionState]:
        return self.cache.get(key)

    def update_state(self, key: str, updated_state: TranscriptionState):
        # Update an existing TranscriptionState instance in the cache
        if key in self.cache:
            if not isinstance(updated_state, TranscriptionState):
                raise ValueError("transcripts_state_code.TranscriptionStates.updatate_state: updated_state must be an instance of TranscriptionState.")
            self.cache[key] = updated_state
        else:
            raise KeyError(f"No state found for key: {key}")

    def remove_state(self, key: str):
        logger.debug(f"transcripts_state_code.TranscriptionStates.removed_state: {key} removed from cache.")
        if key in self.cache:
            del self.cache[key]

    def make_key(self, audio_input: AudioProcessRequest) -> str:
        name_part = audio_input.youtube_url if audio_input.youtube_url else os.path.basename(audio_input.file.filename)
        quality_part = audio_input.audio_quality
        key = name_part + "_" + quality_part
        return key

# initialize global access to state storage.

states = TranscriptionStates()



def initialize_transcription_state(audio_input: AudioProcessRequest) -> TranscriptionState:
    logger.debug(f"transcripts_state_code.initialize_transcription_state: audio_input: {audio_input}")

    # The client comes in with an audio_input property. The key is based on this.
    key = states.make_key(audio_input)
    state = states.get_state(key)
    logger.debug(f"transcripts_state_code.initialize_transcription_state: state key is: {key}")
    # Does audio+quality already have content?
    if state:
        # The wind is at this audio's back...
        logger.debug("transcripts_state_code.initialize_transcription_state: state is alredy in the cache.")
    else:
        logger.debug("transcripts_state_code.initialize_transcription_state: state is not in the cache. Getting the metadata.")
        extractor = MetadataExtractor()
        metadata = extractor.extract_metadata(audio_input)
        # Add in the audio quality and compute type as the hf mappings.
        hf_model = AUDIO_QUALITY_MAP[audio_input.audio_quality]
        hf_compute_type = COMPUTE_TYPE_MAP[audio_input.audio_quality]
        # Save as much state as we know.
        local_mp3 = audio_input.local_mp3 if audio_input.local_mp3 else None
        youtube_url = audio_input.youtube_url if audio_input.youtube_url else None
        # The chapters don't have transcripts in them yet.
        state = TranscriptionState(local_mp3=local_mp3, youtube_url=youtube_url, audio_quality=audio_input.audio_quality, metadata=metadata, hf_model=hf_model, hf_compute_type=hf_compute_type)

    states.add_state(key, state, logger)
    send_message("status","transcription_state_code.initialize_transcription_state: Transcription state has been initialized.",logger)
    return state
