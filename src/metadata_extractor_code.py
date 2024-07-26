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
from exceptions_code import MetadataExtractionException
from logger_code import LoggerBase
from audio_handler_code import AudioHandler
from youtube_handler_code import YouTubeHandler
from dotenv import load_dotenv

load_dotenv()
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class MetadataExtractor:
    async def extract_metadata_and_chapter_dicts(self, audio_input):
        handler = self.get_handler(audio_input)
        try:
            metadata, chapters, audio_filepath = await handler.extract()
        except Exception as e:
            raise MetadataExtractionException("Error extracting metadata") from e
        return metadata, chapters, audio_filepath

    def get_handler(self, audio_input):
        if audio_input.youtube_url:
            return YouTubeHandler(audio_input)
        elif audio_input.audio_file:
            return AudioHandler(audio_input)
        else:
            raise AttributeError("audio_input does not have a supported attribute")
