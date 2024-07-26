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
from dotenv import load_dotenv
load_dotenv()

from fastapi import UploadFile
from pathvalidate import validate_filename, validate_filepath, ValidationError
from pydantic import BaseModel, Field, field_validator
import torch
from typing import Optional

from logger_code import LoggerBase

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)


LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

# Audio formats that can be processed by the whisper model.
SUPPORTED_AUDIO_FORMATS = {'.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.opus'}

AUDIO_QUALITY_MAP = {
    "default":  "tiny.en",
    "tiny": "tiny.en",
    "small": "small.en",
    "medium": "medium.en",
    "large": "large-v3"
}

COMPUTE_TYPE_MAP = {
    "default": torch.float16,
    "float16": torch.float16,
    "float32": torch.float32,
}

class AudioProcessRequest(BaseModel):
    youtube_url: Optional[str] = Field(None, description="YouTube URL to download audio from. Input requires either a YouTube URL or mp3 file.")
    audio_file: Optional[str] = Field(None, description="The stored local audio file.")
    audio_quality: str = Field(default="default", description="Audio quality setting for processing.")

    @field_validator('audio_file')
    def is_valid_audio_file_path(cls, v):
        # Note: Audio file can be None if a YouTube URL is provided.
        if v is None:
            return None
        try:
            validate_filepath(file_path=v, platform='auto')
        except ValidationError as e:
            raise ValueError(f"{v} is not a valid file path. {e}")
        try:
            filename = os.path.basename(v)
            validate_filename(filename, platform='auto')
        except ValidationError as e:
            raise ValueError(f"{v} is not a valid file path.")
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

def save_local_audio_file(upload_file: UploadFile):
    # Ensure the local directory exists
    if not os.path.exists(LOCAL_DIRECTORY):
        os.makedirs(LOCAL_DIRECTORY)

    file_location = os.path.join(LOCAL_DIRECTORY, upload_file.filename)
    if not os.path.exists(file_location):
        with open(file_location, "wb+") as file_object:
            file_object.write(upload_file.file.read())
            file_object.close()
        logger.debug(f"File saved to {file_location}")
    else:
        logger.debug(f"File {file_location} already exists.")
    return file_location
