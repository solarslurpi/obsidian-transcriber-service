import asyncio
import logging
import os
import re
import yt_dlp
from functools import partial
from typing import List, Tuple
from exceptions_code import ProgressHookException
from global_stuff import global_message_queue
from logger_code import LoggerBase
from metadata_shared_code import MetadataMixin, Metadata
from utils import format_sse

from dotenv import load_dotenv

load_dotenv()
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

def progress_hook(info_dict, queue, loop):
    if info_dict['status'] in ['finished', 'downloading']:
        try:
            default_message = info_dict['_default_template']
            message = re.sub(r'\x1b\[.*?m', '', default_message)
            message = re.sub(r'\s+', ' ', message).strip()
            message = format_sse("status", message)
            logger.debug(f"--> progress_hook: {message}")
            # Submit the queue.put coroutine to the main thread's event loop
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
                mp3_filepath = self._set_audio_input_path(info_dict.get('title', 'untitled'))
                metadata = self.build_metadata_instance(info_dict)
                chapter_dicts = info_dict.get('chapters', [])
        except Exception as e:
            logger.error(f"Failed to download video for {url}: {e}")
            raise e

        return metadata, chapter_dicts, mp3_filepath

    def get_ydl_opts(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> dict:
        ydl_opts = {
            'simulate': False,
            'format': 'bestaudio/best',
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

    def _set_audio_input_path(self, title: str) -> str:
        yt_dlp_filename = title + ".mp3"
        mp3_filepath = os.path.join(LOCAL_DIRECTORY, yt_dlp_filename)
        return mp3_filepath
