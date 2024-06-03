import logging
import os
import re
import shutil
from typing import Optional

from fastapi import UploadFile
import torch
from pydantic import BaseModel, Field, model_validator

from logger_code import LoggerBase
from utils import  send_message


logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

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
    local_mp3: Optional[str] = Field(default=None, description="Local storage of mp3 file. This is where the transcription part will look for the audio file.")

    def __init__(self, **data):
        super().__init__(**data)
        if self.file:
            local_mp3_path = os.path.join(f'{LOCAL_DIRECTORY}', self.file.filename)
            with open(local_mp3_path, 'wb') as buffer:
                shutil.copyfileobj(self.file.file, buffer)
            self.local_mp3 = local_mp3_path


    @model_validator(mode='after')
    def check_youtube_url_or_file(cls, values):
        if values.youtube_url and values.file:
            send_message("error","Please provide either a YouTube URL or an MP3 file, not both.")
        elif not values.youtube_url and not values.file:
            send_message("error","No YouTube URL or file provided.")
        if values.youtube_url:
            if not cls.is_valid_youtube_url(values.youtube_url):
                send_message("error","Invalid YouTube URL provided.")
        return values

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        # Regular expression to validate YouTube URL
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'((watch\?v=)|(embed/)|(v/)|(.+\?v=))?([^&=%\?]{11})')
        return youtube_regex.match(url) is not None
