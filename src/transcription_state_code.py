import logging
import os
import shutil
from typing import Optional, List

from fastapi import UploadFile
from pydantic import BaseModel, Field


from logger_code import LoggerBase
from metadata_code import MetadataExtractor
from audio_processing_model import AudioProcessRequest
from youtube_download_code import YouTubeDownloader

# Create a logger named after the module
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "default_local_directory")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)



class Chapter(BaseModel):
    title: str = Field(..., description="Title of the chapter.")
    start: int = Field(..., description="Start time of the chapter in seconds.")
    end: int = Field(..., description="End time of the chapter in seconds.")
    transcription: Optional[str] = Field(None, description="Transcription for the chapter.")

class TranscriptionState(BaseModel):
    # Manages the state and behavior of a single transcription.
    local_mp3: Optional[str] = Field(default=None, description="Local storage of mp3 file. This is where the transcription part will look for the audio file.")
    youtube_url: Optional[str] = Field(default=None, description="URL of the YouTube video. ")
    audio_quality: str = Field(default="default", description="Determines what size model the whisper transcription will use. The larger model will produce better results at a high compute and time cost.")
    compute_type: str = Field(default="default", description="Either float16 or float32.")
    metadata: str = Field(default="default", description="YAML formatted.  Used for Obisidan frontmatter.  YouTube metadata is very rich.  mp3 file is not so rich in metadata..")
    chapters: List[Chapter] = Field(default_factory=list, description="List of chapters with start and end times and transcriptions.")
    transcription_time: int = Field(default=0,description="Number of seconds it took to transcribe the audio file.")
    transcript_done: bool = Field(default=False, description="True if the transcription is complete.")

    @property
    def num_chapters_with_transcripts(self) -> int:
        return sum(1 for chapter in self.chapters if chapter.transcription)

    @property
    def num_chapters_total(self) -> int:
        return len(self.chapters)

    def add_chapter(self, title: str, start: int, end: int, transcription: Optional[str] = None) -> None:
        self.chapters.append(Chapter(title=title, start=start, end=end, transcription=transcription))

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

# initialize global access to state storage.

states = TranscriptionStates()

def get_audio_input_key(audio_input: AudioProcessRequest) -> str:
    if audio_input.youtube_url:
        logger.debug(f"transcripts_state_code.get_audio_input_key: Audio input is a youtube video: {audio_input.youtube_url}.")
        return f"{audio_input.youtube_url}_{audio_input.audio_quality}"
    elif audio_input.file:
        logger.debug(f"transcripts_state_code.get_audio_input_key: Audio input is an uploaded mp3 file: {audio_input.file.filename}.")
        return f"{audio_input.file.filename}_{audio_input.audio_quality}"
    else:
        raise ValueError("Either youtube_url or file must be provided in the request.")

def initialize_transcription_state(audio_input: AudioProcessRequest) -> TranscriptionState:
    logger.debug(f"transcripts_state_code.initialize_transcription_state: audio_input: {audio_input}")

    # The client comes in with an audio_input property. The key is based on this.
    key = get_audio_input_key(audio_input)
    state = states.get_state(key)
    logger.debug(f"state key is: {key}")
    # Does the bin already have content?
    if state:
        # The wind is at this audio's back...
        logger.debug("state is alredy in the cache.")
        # Start the transcription process.
    else:
        extractor = MetadataExtractor()
        # When creating, add in what the client has given us into the state instance.
        if YouTubeDownloader.is_youtube_url(audio_input):
            # Instantiate a new state with all the info we can.
            try:
                metadata = extractor.extract_youtube_metadata(youtube_url=audio_input.youtube_url, audio_quality=audio_input.audio_quality)
                logger.debug("transcription_state_code.initialize_transcription_state: Metadata has been extracted from a YouTube video.")
                state = TranscriptionState(youtube_url=audio_input.youtube_url, audio_quality=audio_input.audio_quality, metadata=metadata)
            except Exception as e:
                logger.error(f"Error extracting YouTube metadata: {e}")
                raise Exception(f"Failed to extract YouTube metadata for URL {audio_input.youtube_url}: {e}")
        else:
            # Save the uploaded file to a local directory. This way we are all ready to go to the next step.
            metadata = extractor.extract_mp3_metadata(mp3_filepath=audio_input.local_mp3, audio_quality=audio_input.audio_quality)
            state = TranscriptionState(local_mp3=audio_input.local_mp3, audio_quality=audio_input.audio_quality)
            logger.debug(f"state starts as uploaded mp3 file: {audio_input.youtube_url}.")
            state = TranscriptionState(local_mp3=audio_input.local_mp3, audio_quality=audio_input.audio_quality, metadata=metadata)
    states.add_state(key, state, logger)
    return state
