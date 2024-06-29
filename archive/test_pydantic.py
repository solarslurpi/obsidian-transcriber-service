import asyncio
from audio_processing_model import AudioProcessRequest
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

# class AudioProcessRequest(BaseModel):
#     youtube_url: Optional[str] = None
#     file: Optional[str] = None  # Simplified for this example
#     audio_quality: str = Field(default="default", description="Audio quality setting for processing.")

#     @field_validator('youtube_url')
#     def check_youtube_url(cls, v):
#         if v is not None and not cls.is_valid_youtube_url(v):
#             raise ValueError("OOPS! The YouTube URL provided is not valid. Please provide a valid YouTube URL.")
#         return v

#     @staticmethod
#     def is_valid_youtube_url(url: str) -> bool:
#         youtube_regex = re.compile(
#             r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
#             r'((watch\?v=)|(embed/)|(v/)|(.+\?v=))?([^&=%\?]{11})')
#         return youtube_regex.match(url) is not None


def test_audio_process_request():
    try:
        # Test with an invalid URL
        audio_input = AudioProcessRequest(
            youtube_url="junk_url",
            audio_quality="default"
        )
    except Exception as e:
        print(f"Validation failed: {e}")


async def async_test_audio_process_request():
    try:
        # Test with an invalid URL
        audio_input = AudioProcessRequest(
            youtube_url="junk_url",
            audio_quality="default"
        )
    except Exception as e:
        print(f"Validation failed: {e.errors()[0].get('msg','msg attribute not found')}")

# Run the test
# test_audio_process_request()

# Run the async test
asyncio.run(async_test_audio_process_request())

# Validation failed: 1 validation error for AudioProcessRequest
# youtube_url
#   OOPS! The YouTube URL provided is not valid. Please provide a valid YouTube URL. (type=value_error)
