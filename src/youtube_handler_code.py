import asyncio
from functools import partial
import logging
import os
import re
import yt_dlp
from typing import List, Tuple
from exceptions_code import ProgressHookException, YouTubeDownloadException
from global_stuff import global_message_queue
from logger_code import LoggerBase
from metadata_shared_code import MetadataMixin, Metadata
from utils import format_sse, send_sse_message

from dotenv import load_dotenv

load_dotenv()
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

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

class YouTubeHandler(MetadataMixin):
    def __init__(self, audio_input):
        self.audio_input = audio_input

    async def extract(self) -> Tuple[Metadata, List, str]:
        """
        Extracts metadata and audio from a YouTube video synchronously.
        """
        loop = asyncio.get_event_loop()
        download_task = asyncio.create_task(self.download_video(self.audio_input.youtube_url, global_message_queue, loop))
        # The transcription can't start until the download is complete. So... wait for it.
        metadata, chapter_dicts, mp3_filepath = await download_task
        return metadata, chapter_dicts, mp3_filepath

    async def download_video(self, url: str, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> Tuple[Metadata, List, str]:
        ydl_opts = self.get_ydl_opts(queue, loop)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = await loop.run_in_executor(None, ydl.extract_info, url, True)
                # Go through the tags list in info_dict and replace spaces within each tag with underscores.
                if 'tags' in info_dict:
                    info_dict['tags'] = [re.sub(r'\s+', '_', tag) for tag in info_dict['tags']]
                potential_problems_filepath = info_dict['requested_downloads'][0]['filepath']
                logger.debug(f"The file: {potential_problems_filepath} exists: {os.path.exists(potential_problems_filepath)}")
                sanitized_filename = re.sub(r'[:]', '-', info_dict['title'])  # Replace colon with hyphen
                sanitized_filename = re.sub(r'[\<\>\"/|?*]', '', sanitized_filename)  # Remove other problematic
                mp3_filepath = LOCAL_DIRECTORY + '/' + sanitized_filename + '.mp3'
                try:
                    os.rename(potential_problems_filepath, mp3_filepath)
                except FileExistsError:
                    logger.warning(f"Warning: The file '{mp3_filepath}' already exists.")
                # add in the audio quality.
                info_dict['audio_quality'] = self.audio_input.audio_quality
                metadata = self.build_metadata_instance(info_dict)
                chapter_dicts = info_dict.get('chapters', [])
                if not chapter_dicts:
                    chapter_dicts = [{'title': info_dict.get('title',''), 'start_time': 0.0, 'end_time': 0.0}]
        except YouTubeDownloadException as e:
            logger.error(f"Failed to download video for {url}: {e}")
            raise e

        return metadata, chapter_dicts, mp3_filepath

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


    # def _sanitize_filename(self, current_mp3_filepath: str) -> str:
    #     def cleaned_name(uncleaned_name:str) -> str:
    #         # Remove non-alphanumeric characters except for spaces, periods, and hyphens.
    #         cleaned_name = re.sub(r"[^a-zA-Z0-9 \.-]", "", uncleaned_name)
    #         # Replace spaces with underscores.
    #         cleaned_name = cleaned_name.replace(" ", "_")
    #         # Replace full-width colons and standard colons with a hyphen or other safe character
    #         cleaned_name = cleaned_name.replace('：', '_').replace(':', '_')
    #         return cleaned_name

    #     current_mp3_basename = os.path.splitext(os.path.basename(current_mp3_filepath))[0]
    #     cleaned_mp3_filename = cleaned_name(current_mp3_basename) + ".mp3"
    #     cleaned_mp3_filepath = os.path.join(LOCAL_DIRECTORY, cleaned_mp3_filename)
    #     os.rename(current_mp3_filepath,cleaned_mp3_filepath)
    #     return cleaned_mp3_filepath
