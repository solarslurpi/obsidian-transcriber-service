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
import os

import ctranslate2
from faster_whisper import WhisperModel


import logging_config
from exceptions_code import TranscriberException
from transcription_state_code import Chapter
from utils import send_sse_message

# Create a logger instance for this module
logger = logging.getLogger(__name__)

# This is for storing the temporary audio slice when the audio is divided into chapters.
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

class TranscribeAudio:
    def __init__(self, audio_quality:str="default", compute_type:str="int8", chapter_time_chunk:int=10):
        self.chapter_time_chunk = chapter_time_chunk
        # Load the model
        try:
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
            logger.debug(f"GPU found: {device == 'cuda'}")
            self.model =  WhisperModel(audio_quality, device= device, compute_type=compute_type)
            # whisper.load_model(audio_quality)
            logger.debug(f"Model loaded. Size: {audio_quality}")
        except Exception as e:
            logger.error(f"Error loading model. {e}")
            raise TranscriberException(f"Error loading model. {e}")

    async def transcribe(self, audio: str, state_chapters: list[Chapter] = None) -> str:
        # whisper is not thread safe.  It does not like to reuse a loaded model.
        logging.debug(f"--->Start Transcription for {audio}")

        # Returns a generator
        segments, info = self.model.transcribe(audio, beam_size=5)
        total_duration = info.duration_after_vad
        await send_sse_message("status", f"Content length:  {format(total_duration, '.0f')} seconds.")
        logger.debug(f"total_duration: {total_duration}")
        chapters = await self.break_audio_into_chapters(segments, total_duration, state_chapters)
        logger.debug(f"<---Done transcribing {audio}.")
        return chapters

    async def break_audio_into_chapters(self, segments, total_duration, state_chapters):
        chapter_duration = self.chapter_time_chunk * 60   # in seconds
        if self._is_short_audio(state_chapters, total_duration, chapter_duration):
            return self._create_single_chapter(segments)
        if self._is_broken_into_chapters(state_chapters):
            return await self._create_chapters_from_metadata(segments, state_chapters, total_duration)
        else:
            return await self._create_time_based_chapters(segments, chapter_duration, total_duration)

    def _is_short_audio(self, state_chapters, total_duration, chapter_duration):
        if self._is_broken_into_chapters(state_chapters) or total_duration > chapter_duration:
            return False
        return True

    def _is_broken_into_chapters(self, state_chapters):
        if len(state_chapters) > 0 and state_chapters[0].end_time != 0:
            return True
        return False

    def _create_single_chapter(self, segments):
        """Create a single chapter for short audio."""
        results = list(segments)
        text = ' '.join([segment.text for segment in results])
        chapter = Chapter(start_time=round(results[0].start, 2), end_time=round(results[-1].end, 2), text=text, number=1)
        return [chapter]

    async def _create_time_based_chapters(self, segments, chapter_duration, total_duration):
        # Start a new chapter
        chapters = []
        new_end_time = chapter_duration
        current_chapter = Chapter(start_time=0.0, end_time=round(new_end_time,2), text='', number=1)
        chapter_number = 1
        # Go through the generator
        for segment in segments:
            logger.debug("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            if segment.start >= new_end_time:
                # We've reached the end of a timed chapter. Append it to the list.
                chapters.append(current_chapter)
                # Start on a new chapter.  The end time is determined by the segments that will be added.
                logger.debug(f"---Chapter {chapter_number} appended. on to chapter {chapter_number+1}segment start: {segment.start} ---")
                chapter_number += 1
                current_chapter = Chapter(start_time=segment.start, end_time=0.0, text='', number=chapter_number)
                new_end_time = segment.end + chapter_duration
                percent_complete = round((segment.end / total_duration) * 100)
                await send_sse_message("status", f"Transcribed {percent_complete}%")

            else:
                # Add the text to the current chapter
                current_chapter.text += segment.text
                # Keep track of the end time of the last segment in the chapter to use as a chapter endpoint when appending the chapter.
                current_chapter.end_time = round(segment.end,2)

        # Add the last chapter
        if current_chapter.text:
            chapters.append(current_chapter)

        return chapters

    async def _create_chapters_from_metadata(self, segments, state_chapters, total_duration):
        for index, chapter in enumerate(state_chapters):
            logger.debug(f"Chapter {index}: {chapter.start_time} -> {chapter.end_time}")
            chapter_segments = []
            for segment in segments:
                logger.debug(f"Segment: {segment.start} -> {segment.end}")
                if segment.end >= chapter.end_time:
                    # We've got all the segments for the chapter. It may not be event so, we'll also set the chapter end_time..
                    end_time = round(segment.end,2)
                    chapter.end_time = end_time
                    chapter.text = ' '.join(segment.text for segment in chapter_segments)
                    chapter.number = index+1
                    # We need to set the start of the next chapter to the end of the segment.
                    if index+1 < len(state_chapters):
                        state_chapters[index+1].start_time = end_time
                    percent_complete = round((segment.end / total_duration) * 100)
                    await send_sse_message("status", f"Transcribed {percent_complete}%")
                    break
                # If the start time of the segment is within the start and end times of a chapter, add the segments to the
                # chapter_segments list.
                if chapter.start_time <= segment.start < chapter.end_time:
                    chapter_segments.append(segment)

            continue
        # The last chapter may not have been processed
        if len(chapter_segments) > 0:
            state_chapters[-1].text = ' '.join(segment.text for segment in chapter_segments)
            state_chapters[-1].number = len(state_chapters)
            state_chapters[-1].start_time = round(chapter_segments[0].start,2)
        return state_chapters