
import logging
import os
import re
from dotenv import load_dotenv
load_dotenv()

from fastapi import UploadFile
from pydantic import BaseModel, Field, field_validator
import torch
from typing import Optional



from logger_code import LoggerBase

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)


LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists


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

class AudioProcessRequest(BaseModel):
    youtube_url: Optional[str] = Field(None, description="YouTube URL to download audio from. Input requires either a YouTube URL or mp3 file.")
    mp3_file: Optional[str] = Field(None, description="The stored local mp3 file.")
    audio_quality: str = Field(default="default", description="Audio quality setting for processing.")


    @field_validator('youtube_url')
    def check_youtube_url(cls, v):
        if v is not None and not cls.is_valid_youtube_url(v):
            raise ValueError(f"{v} is not valid. Please provide a valid YouTube URL.")
        return v

    @field_validator('audio_quality')
    def is_valid_audio_quality(cls,v):
        # Remove and new lines or blanks at beginning and end of the string
        v = v.strip(" \n")
        # Verify that the audio quality is one of the keys in the AUDIO_QUALITY_MAP
        if v not in AUDIO_QUALITY_MAP.keys():
            logger.warning(f"{v} is not a valid audio quality. Defaulting to 'default' audio quality.")
            return "default"
        return v

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'((watch\?v=)|(embed/)|(v/)|(.+\?v=))?([^&=%\?]{11})')
        return youtube_regex.match(url) is not None


def save_local_mp3(upload_file: UploadFile):
    # Ensure the local directory exists
    if not os.path.exists(LOCAL_DIRECTORY):
        os.makedirs(LOCAL_DIRECTORY)

    file_location = os.path.join(LOCAL_DIRECTORY, upload_file.filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(upload_file.file.read())
        file_object.close()
    logger.debug(f"audio_processing_model.save_local_mp3: File saved to {file_location}")
    return file_location
