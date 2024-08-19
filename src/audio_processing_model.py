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
import logging
import os
import re

from fastapi import  HTTPException
from pathvalidate import validate_filepath, ValidationError
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional

# Create a logger instance for this module
logger = logging.getLogger(__name__)


# Audio formats that can be processed by the whisper model.
SUPPORTED_AUDIO_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.opus'}


AUDIO_QUALITY_MAP = {
    "default":  "Systran/faster-whisper-tiny.en",
    "tiny": "Systran/faster-whisper-tiny.en",
    "small": "Systran/faster-distil-whisper-small.en",
    "medium": "Systran/faster-distil-whisper-medium.en",
    "large": "Systran/faster-distil-whisper-large-v3"
}
# see https://opennmt.net/CTranslate2/quantization.html
COMPUTE_TYPE_LIST = ["int8", "float16", "float32", "int8_float32", "int8_float16", "int8_bfloat16", "int16", "bfloat16"]

class AudioProcessRequest(BaseModel):
    youtube_url: Optional[str] = Field(None, description="YouTube URL to download audio from. Input requires either a YouTube URL or mp3 file.")
    audio_filename: Optional[str] = Field(None, description="The basename of the audio file sent through upload_file.")
    audio_quality: str = Field(default="default", description="Audio quality setting for processing.")
    compute_type: str = Field(default="int8", description="Compute type for processing.")
    chapter_chunk_time: int = Field(default=10, description="Time chunk in minutes for dividing audio into chapters.")


    @model_validator(mode='before')
    @classmethod
    def check_audio_source(cls, values):
        youtube_url = values.get('youtube_url')
        audio_filename = values.get('audio_filename')
        if youtube_url is not None and audio_filename is not None:
            raise HTTPException(status_code=400, detail="Both youtube_url and file cannot have values.")
        elif youtube_url is None and audio_filename is None:
            raise HTTPException(status_code=400, detail="Need either a YouTube URL or mp3 file.")

        return values

    @field_validator('audio_filename')
    def is_valid_audio_file_path(cls, v):
        # Note: Audio file can be None if a YouTube URL is provided.
        if v is None:
            return None
        try:
            validate_filepath(file_path=v, platform='auto')
        except ValidationError as e:
            raise ValueError(f"{v} is not a valid file path. {e}")

        file_extension = os.path.splitext(v)[1].lower()
        if file_extension not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError(f"{v} has an unsupported audio format. Supported formats are: {', '.join(SUPPORTED_AUDIO_FORMATS)}")
        return v

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
        if v not in AUDIO_QUALITY_MAP.keys() or v == "default":
            audio_quality = AUDIO_QUALITY_MAP["default"]
            logger.debug(f"{v} will be converted to {audio_quality}.")
            return audio_quality
        return v

    @field_validator('compute_type')
    def is_valid_compute_type(cls,v):
        # Remove and new lines or blanks at beginning and end of the string
        v = v.strip(" \n")
        # Verify that the compute_type is in the list of supported compute types.
        if v not in COMPUTE_TYPE_LIST:
            compute_type = COMPUTE_TYPE_LIST[0]
            logger.debug(f"{v} is not a valid compute type. Defaulting to {compute_type}.")

            return compute_type
        return v

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'((watch\?v=)|(embed/)|(v/)|(.+\?v=))?([^&=%\?]{11})')
        return youtube_regex.match(url) is not None
