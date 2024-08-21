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
import asyncio
import logging

import logging_config
from exceptions_code import MetadataExtractionException
from audio_handler_code import AudioHandler
from utils import get_audio_directory
from youtube_handler_code import YouTubeHandler



# Create a logger instance for this module
logger = logging.getLogger(__name__)


class MetadataExtractor:
    async def extract_metadata_and_chapter_dicts(self, audio_input):
        handler = self.get_handler(audio_input)
        try:
            audio_directory = get_audio_directory()
            metadata, chapters, audio_filename = await handler.extract(audio_directory)
        except Exception as e:
            raise MetadataExtractionException("Error extracting metadata") from e
        return metadata, chapters, audio_filename

    def get_handler(self, audio_input):
        if audio_input.youtube_url:
            return YouTubeHandler(audio_input)
        elif audio_input.audio_filename:
            return AudioHandler(audio_input)
        else:
            raise AttributeError("audio_input does not have a supported attribute")
