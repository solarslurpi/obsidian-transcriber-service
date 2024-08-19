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
from audio_processing_model import  AudioProcessRequest
from pydantic import BaseModel, Field

from utils import format_time


class Metadata(BaseModel):
    audio_input: Optional[AudioProcessRequest] = Field(default=None, description="YouTube URL or audio filepath as well as audio_quality.")
    title: Optional[str] = Field(default=None, description="Title field as it is in index_dict. It will be the YouTube title or the basefilename of the mp3 file.")
    tags: Optional[str] = Field(default=None, description="Tags associated with the metadata. The CustomStr annotation is used to convert the list of tags provided by YouTube to a string.")
    description: Optional[str] = Field(default=None, description="Description associated with the metadata.")
    duration: Optional[str] = Field(default=None, description="Duration of the audio in hh:mm:ss.")
    channel: Optional[str] = Field(default=None, description="channel name")
    upload_date: Optional[str] = Field(default=None, description="upload date")
    uploader_id: Optional[str] = Field(default=None, description="uploader id")
    download_time: Optional[str] = Field(default=None, description="Number of seconds it took to download the YouTube Video.")
    transcription_time: Optional[str] = Field(default=None, description="Number of seconds it took to process the transcription.")


def build_metadata_instance(info_dict: Dict) -> Metadata:

    info_dict['duration'] = format_time(info_dict.get('duration', 0))
    return Metadata(**info_dict)
