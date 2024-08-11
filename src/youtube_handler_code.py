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
from functools import partial
import logging
import os
import re
import yt_dlp
from typing import List, Tuple

import logging_config
from exceptions_code import ProgressHookException, YouTubeDownloadException, YouTubePostProcessingException
from global_stuff import global_message_queue
from metadata_shared_code import Metadata

from utils import format_sse

from dotenv import load_dotenv

load_dotenv()
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
YOUTUBE_CACHE_FILEPATH = os.path.join(os.getenv("YOUTUBE_CACHE_DIRECTORY", "youtube_cache"), "youtube_cache.json")
# Create a logger instance for this module
logger = logging.getLogger(__name__)

def progress_hook(info_dict, queue, loop):
    if info_dict['status'] in ['finished', 'downloading']:
        try:
            default_message = info_dict['_default_template']
            # Remove ANSI escape sequences from the message
            message = re.sub(r'\x1b\[.*?m', '', default_message)
            # Remove multiple spaces and leading/trailing spaces
            message = re.sub(r'\s+', ' ', message).strip()
            # Format a status message to send to the client in the form of an SSE message.
            message = format_sse("status", message)
            logger.debug(f"--> progress_hook: {message}")
            # Submit the queue.put() coroutine to the main thread's event loop
            # so that event_generator can send the sse message.
            asyncio.run_coroutine_threadsafe(queue.put(message), loop)
        except ProgressHookException as e:
            print(f'Error: {e}')
            raise e

class YouTubeHandler():
    def __init__(self, audio_input):
        self.audio_input = audio_input

    async def extract(self) -> Tuple[dict, List, str]:
        """
        Extracts metadata and audio from a YouTube video synchronously.
        """
        loop = asyncio.get_event_loop()
        logger.info(f"--->Starting YouTube download of {self.audio_input.youtube_url}")
        download_task = asyncio.create_task(self.download_video(self.audio_input.youtube_url, global_message_queue, loop))
        # The transcription can't start until the download is complete. So... wait for it.
        metadata_dict, chapter_dicts, mp3_filepath = await download_task
        logger.info(f"<---Done downloading {self.audio_input.youtube_url}")
        return metadata_dict, chapter_dicts, mp3_filepath

    async def download_video(self, url: str, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> Tuple[Metadata, List, str]:
        ydl_opts = self.get_ydl_opts(queue, loop)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # The info that can be extracted is listed at https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#output-template
                    info_dict = await loop.run_in_executor(None, ydl.extract_info, url, True)
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"Failed to download video for {url}: {e}")
                    raise YouTubeDownloadException(f"Failed to download video for {url}: {e}")
                except yt_dlp.utils.PostProcessingError as e:
                    logger.error(f"Failed to post-process video for {url}: {e}")
                    raise YouTubePostProcessingException(f"Failed to post-process video for {url}: {e}")
                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                # Go through the tags list in info_dict and replace spaces within each tag with underscores.
                if 'tags' in info_dict: # tags are a list.
                    tags_list = [re.sub(r'\s+', '_', tag) for tag in info_dict['tags']]
                    info_dict['tags'] = ', '.join(tags_list)
                # Add in the YouTube url
                info_dict['youtube_url'] = url
                potential_problems_filepath = info_dict['requested_downloads'][0]['filepath']
                logger.debug(f"The file: {potential_problems_filepath} exists: {os.path.exists(potential_problems_filepath)}")
                sanitized_filename = re.sub(r'[:]', '-', info_dict['title'])  # Replace colon with hyphen
                sanitized_filename = re.sub(r'[\<\>\"/|?*]', '', sanitized_filename)  # Remove other problematic
                mp3_filepath = LOCAL_DIRECTORY + '/' + sanitized_filename + '.mp3'
                if not os.path.exists(mp3_filepath):
                    os.rename(potential_problems_filepath, mp3_filepath)
                # add in the audio quality.
                info_dict['audio_quality'] = self.audio_input.audio_quality
                chapter_dicts = info_dict.get('chapters', [])
                if not chapter_dicts:
                    chapter_dicts = [{'title': info_dict.get('title',''), 'start_time': 0.0, 'end_time': 0.0}]
        except YouTubeDownloadException as e:
            logger.error(f"Failed to download video for {url}: {e}")
            raise e
        # Lose the properties yt-dlp adds that we don't need by converting to a Metadata object.

        return info_dict, chapter_dicts, mp3_filepath

    def get_ydl_opts(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> dict:
        ydl_opts = {
            'logger': logger,
            'verbose': True, # Enable verbose logging for debugging.
            'replace-in-metadata': { # NOTE: I SPENT TIME I CAN'T GET BACK trying to figure out why this property isnt working.
            'title': {'：': '_', ':': '_'},  # Replace full-width and standard colons
            },
            'simulate': False,
            'format': 'bestaudio/best',
            'restrict-filenames': True,
            'outtmpl': os.path.join(LOCAL_DIRECTORY, '%(title)s.%(ext)s'),
            'quiet': True,
            'progress_hooks': [partial(progress_hook, queue=queue, loop=loop)],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '96',
            }],
            'postprocessor_args': [
                '-ac', '1',
                '-ar', '44100'
            ],
        }
        return ydl_opts
