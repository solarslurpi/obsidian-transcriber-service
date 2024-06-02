from typing import Optional, List, Dict, Union

import torch
from fastapi import UploadFile, Form, File
from pydantic import BaseModel, Field
AUDIO_QUALITY_MAP = {
    "default":  "openai/whisper-tiny.en",
    "tiny": "openai/whisper-tiny.en",
    "small": "openai/whisper-small.en",
    "medium": "openai/whisper-medium.en",
    "large": "openai/whisper-large-v3"
}

COMPUTE_TYPE_MAP = {
    "default": torch.float16,
    "float16": torch.float16,
    "float32": torch.float32,
}
# Define the blueprint for the input data.  Note that the input
# is either a YouTube URL or an UploadFile.  Both are optional
# to allow for one or the other.
class AudioProcessRequest(BaseModel):
    youtube_url: Optional[str] = None
    file: Optional[UploadFile] = None
    audio_quality: str = Field(default="default", description="Audio quality setting for processing.")
# This dependency function - i.e.: depends(as_form) - Tell FastAPI that
# the data is being passed in as a form. Look for one or both or neither
# of these fields.
def as_form(
    youtube_url: str = Form(None),  # Use Form to specify form data
    file: UploadFile = File(None),  # Use File to specify file upload
    audio_quality: str = Form(default="default", description="Audio quality setting for processing.  Comes in as good/better/best.")
) -> AudioProcessRequest:
    return AudioProcessRequest(youtube_url=youtube_url, file=file, audio_quality= audio_quality)

class GlobalState(BaseModel):
    isYouTube_url: bool = Field(default=False, description="True if the original source of the mp3 file was YouTube, False if it was a local file.")
    youtube_url: str = Field(default=None, description="URL of the downloaded YouTube video.")
    basefilename: str = Field(default=None, description="Name from YouTube title or mp3 filename for Obsidian transcription filename base.")
    mp3_filepath: str = Field(default=None, description="Location of the MP3 file.")
    audio_quality: str = Field(default="default", description="Used to map to an OpenAI Whisper model during audio to text (asr).")
    compute_type: str = Field(default="default", description="Used by the OpenAI Whisper model during audio to text (asr).")
    yaml_metadata: str = Field(default="default", description="A YouTube video's metadata to be used as Obsidian frontmatter (YAML).")
    chapters: list = Field(default_factory=list, description="Start and end time of different chapters/topics in the transcript.")
    transcription_time: int = Field(default=0,description="Number of seconds it took to transcribe the audio file.")
    transcript_done: bool = Field(default=False, description="True if the transcription is complete.")

    def reset(self):
        self.isYouTube_url = False
        self.youtube_url = None
        self.basefilename = None
        self.mp3_filepath = None
        self.audio_quality = "default"
        self.compute_type = "default"
        self.yaml_metadata = None
        self.chapters = []
        self.transcription_time = 0
        self.transcript_done = False


    def update(self,**kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Instance of the global state
global_state = GlobalState()
# ----------------------------------------------------------------------------------------------------
