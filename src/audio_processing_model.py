
import logging
import re

from typing import Optional

import torch
from pydantic import BaseModel, Field, field_validator

from logger_code import LoggerBase

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

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
    youtube_url: Optional[str] = None
    file: Optional[str] = None  # Simplified for this example
    audio_quality: str = Field(default="default", description="Audio quality setting for processing.")

    @field_validator('youtube_url')
    def check_youtube_url(cls, v):
        if v is not None and not cls.is_valid_youtube_url(v):
            raise ValueError(f"{v} is not valid. Please provide a valid YouTube URL.")
        return v

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'((watch\?v=)|(embed/)|(v/)|(.+\?v=))?([^&=%\?]{11})')
        return youtube_regex.match(url) is not None
