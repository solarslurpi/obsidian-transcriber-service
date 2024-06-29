import logging
import os
import time
import torch
from typing import Optional, List, Tuple, Dict


from pydantic import BaseModel, Field, field_validator

from exceptions_code import KeyException, MetadataExtractionException
from logger_code import LoggerBase
from metadata_extractor_code import MetadataExtractor
from metadata_shared_code import Metadata
from audio_processing_model import AudioProcessRequest, AUDIO_QUALITY_MAP, COMPUTE_TYPE_MAP
from utils import send_sse_message

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class Chapter(BaseModel):
    title: Optional[str] = Field(default=None, description="Title of the chapter.")
    start_time: Optional[float] = Field(default=None, description="Start time of the chapter in seconds.")
    end_time: Optional[float] = Field(default=None, description="End time of the chapter in seconds.")
    transcript: Optional[str] = Field(default=None, description="Transcription of the chapter.")
    number:  Optional[int] = Field(default=None, description="Chapter number.")

class TranscriptionState(BaseModel):
    # Manages the state and behavior of a single transcription.
    key: str = Field(default=None, description="A unique key that allows the client to request the same content again by querying the state with this key.")
    basename: str = Field(default=None, description="Basename of the transcript note to be used by the client when creating the note.")
    local_mp3: str = Field(default=None, description="Local storage of mp3 file. This is where the transcription part will look for the audio file.")
    hf_model: str = Field(default=None, description="Set when initializing state from user's audio_input.audio_quality.")
    hf_compute_type: torch.dtype = Field(default=None, description="Used by transcriber. Either float32 or float16")
    metadata: Metadata = Field(default=None, description="Turned into YAML frontmatter for a (Obsidian) note. YouTube metadata is very rich.  mp3 file is not so rich in metadata..")
    chapters: List[Chapter] = Field(default_factory=list, description="Each entry provides the metadata as well as the transcript text of a chapter of audio content.")
    transcription_time: float = Field(default=0.0,description="Number of seconds it took to transcribe the audio file.")

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

    def update_chapter(self, start: int, transcription: str) -> None:
        for chapter in self.chapters:
            if chapter.start_time == start:
                chapter.transcript = transcription
                break
        else:
            raise ValueError(f"No chapter found with start time {start}")

    def clear_chapters(self) -> None:
        self.chapters = []

    def is_complete(self) -> bool:
        # Check if all required fields (excluding transcription_time) are set
        required_fields = ['key', 'basename', 'local_mp3', 'hf_model', 'hf_compute_type', 'metadata', 'chapters']
        for field in required_fields:
            if getattr(self, field) is None:
                return False
        # Additionally, check that each chapter has transcription_text filled out
        for chapter in self.chapters:
            if not chapter.transcript:
                return False
            return True

    def cleanup(self) -> None:
        """Cleanup resources held by the TranscriptionState."""
        # Clear chapters
        self.clear_chapters()
        # Nullify other fields
        self.local_mp3 = None
        self.key = None
        self.hf_model = None
        self.hf_compute_type = None
        self.metadata = None
        self.transcription_time = 0
        self.transcript_done = False

class ObservableCache(dict):
    def __init__(self, *args, **kwargs):
        super(ObservableCache, self).__init__(*args, **kwargs)
        self._callbacks = []

    def on_change(self, callback):
        self._callbacks.append(callback)

    def __setitem__(self, key, value):
        super(ObservableCache, self).__setitem__(key, value)
        for callback in self._callbacks:
            callback(action="set", key=key, value=value)

    def __delitem__(self, key):
        super(ObservableCache, self).__delitem__(key)
        for callback in self._callbacks:
            callback(action="delete", key=key)

class TranscriptionStates:
    # Manages a collection of multiple TranscriptionState instances.
    def __init__(self):
        self.cache = ObservableCache()
        self.cache.on_change(self.cache_change_callback)

    def cache_change_callback(self, action, key, value=None):
        if action == "set":
            logger.debug(f"STATE: Cache updated - {key}: {value}")
        elif action == "delete":
            logger.debug(f"STATE: Cache item deleted - {key}")

    def add_state(self, key: str, transcription_state: TranscriptionState, logger: LoggerBase):
        '''This method stres an instance of the transcription_state in the cache dictionary with the specified key, making it available for retrieval during subsequent requests, assuming the application's state is preserved between those requests.'''
        if not isinstance(transcription_state, TranscriptionState):
            raise ValueError("transcription_state must be an instance of TranscriptionState.")
        self.cache[key] = transcription_state
        logger.debug(f"transcripts_state_code.TranscriptionStates.add_state: {key} added to cache.")

    def get_state(self, key: str) -> Optional[TranscriptionState]:
        return states.cache.get(key)

    def make_key(self, audio_input: AudioProcessRequest) -> str:
        name_part = audio_input.youtube_url if audio_input.youtube_url else os.path.splitext(os.path.basename(audio_input.mp3_file))[0]
        quality_part = audio_input.audio_quality
        key = name_part + "_" + quality_part
        return key

# initialize global access to state storage.

states = TranscriptionStates()



async def initialize_transcription_state(audio_input: AudioProcessRequest) -> Tuple[TranscriptionState, Metadata]:
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

    logger.debug(f"transcripts_state_code.initialize_transcription_state: audio_input: {audio_input}")

    # The client comes in with an audio_input property. The key is based on this.
    try:
        key = states.make_key(audio_input)
    except KeyException as e:
        await send_sse_message(f"server-error", str(e))
        if state:
            state = None
        return

    state = states.get_state(key)
    # maintain the key for the client in case content is missing.

    logger.debug(f"transcripts_state_code.initialize_transcription_state: state key is: {key}")
    if state:
        logger.debug("transcripts_state_code.initialize_transcription_state: state is alredy in the cache.")
        send_sse_message("status", "Sheer happiness! We already have the content.")
        return state
    else:
        await send_sse_message(event="status", data="Setting up stuff, back shortly!")
        logger.debug("transcripts_state_code.initialize_transcription_state: state is not in the cache. Getting the metadata.")
        extractor = MetadataExtractor()
        try:
            start_time = time.time()
            metadata, chapter_dicts, mp3_filepath = await extractor.extract_metadata_and_chapter_dicts(audio_input)
            chapters = build_chapters(chapter_dicts)
            end_time = time.time()
            metadata.download_time = int(end_time - start_time)
        except MetadataExtractionException as e:
            raise e
        except Exception as e:
            raise
    # Set mp3_filepath to audio_input.mp3_file if not None, else mp3_filepath
    mp3_filepath = audio_input.mp3_file if audio_input.mp3_file else mp3_filepath
    hf_model = AUDIO_QUALITY_MAP[audio_input.audio_quality]
    hf_compute_type = COMPUTE_TYPE_MAP['default']
    # At this point, we have everything except the transcript_text of the chapters.
    try:
        # Write code that gets the basename of mp3_filepath
        filename_no_extension = os.path.splitext(os.path.basename(mp3_filepath))[0]
        state = TranscriptionState(basename=filename_no_extension, local_mp3=mp3_filepath, hf_model=hf_model, hf_compute_type=hf_compute_type,  metadata=metadata, chapters=chapters)
        states.add_state(key, state, logger)
        await send_sse_message(event="status", data="Content has been prepped. All systems go for transcription.")
    except Exception as e:
        raise e
    state.key = key
    return state
