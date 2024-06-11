import asyncio
import logging
import re

import yt_dlp

from exceptions_code import handle_exception, DownloadException
from logger_code import LoggerBase

logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)



# yt_dlp is a synchronous wrapper around youtube-dl. The progress_hook is synchronous.
def youtube_download(youtube_url:str, mp3_filename:str):
    '''downloads the audio from a YouTube video and saves it as an mp3 file.'''
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': mp3_filename ,
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'postprocessor_args': [ # Settings best for transcription
            '-ac', '1', # Convert to mono
            '-ar', '44100' # Set sampling rate to 44.1 kHz
        ]
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except DownloadException as e:
        asyncio.run_coroutine_threadsafe(handle_exception(e, 500, "YouTube download failed."), logger)


# progress_hook must remain synchronous.
def progress_hook(self, d):
    status = d.get('status')

    if status == 'finished':
        # TODO
        pass
    elif status == 'downloading':
        downloaded = d.get('downloaded_bytes')
        total = d.get('total_bytes')
        if total:
            percentage = downloaded / total * 100
    elif status == 'error':
        # TODO
        pass

def sanitize_title(youtube_title: str) -> str:
    # Remove invalid characters
    filename = re.sub(r'[\\/*?:"<>|]', "", youtube_title)
    # Remove leading/trailing white space
    filename = filename.strip()
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    return filename