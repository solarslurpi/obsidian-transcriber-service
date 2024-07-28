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
import os
from typing import Dict, Optional
from audio_processing_model import AUDIO_QUALITY_MAP
from pydantic import BaseModel, Field, field_validator

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

class Metadata(BaseModel):
    youtube_url: Optional[str] = Field(default=None, alias="original_url", description="URL of the YouTube video.")
    title: Optional[str] = Field(default=None, description="Title field as it is in index_dict. It will be the YouTube title or the basefilename of the mp3 file.")
    audio_quality: Optional[str] = Field(default=None, description="Audio quality of the audio file.")
    tags: Optional[str] = Field(default=None, description="Tags associated with the metadata. The CustomStr annotation is used to convert the list of tags provided by YouTube to a string.")
    description: Optional[str] = Field(default=None, description="Description associated with the metadata.")
    duration: Optional[str] = Field(default=None, description="Duration of the audio in hh:mm:ss.")
    channel: Optional[str] = Field(default=None, description="channel name")
    upload_date: Optional[str] = Field(default=None, description="upload date")
    uploader_id: Optional[str] = Field(default=None, description="uploader id")
    download_time: Optional[int] = Field(default=None, description="Number of seconds it took to download the YouTube Video.")
    transcription_time: Optional[int] = Field(default=None, description="Number of seconds it took to transcribe a 'chapter' of an audio file.")

    @field_validator('audio_quality')
    def validate_audio_quality(cls, v):
        if v not in AUDIO_QUALITY_MAP.keys():
            raise ValueError('audio_quality must be a key in AUDIO_QUALITY_MAP.')
        return v

def build_metadata_instance(info_dict: Dict) -> Metadata:
    def _format_time(seconds: float) -> str:
        if not isinstance(seconds, (int, float)):
            return "0:00:00"
        total_seconds = int(seconds)
        mins, secs = divmod(total_seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    info_dict['duration'] = _format_time(info_dict.get('duration', 0))
    return Metadata(**info_dict)
