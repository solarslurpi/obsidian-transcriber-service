import asyncio
import logging
import re

import yt_dlp

from exceptions_code import  DownloadException
from logger_code import LoggerBase
from utils import send_sse_message

logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)



# yt_dlp is a synchronous wrapper around youtube-dl. The progress_hook is synchronous.
def youtube_download(youtube_url:str, mp3_filename:str):
    '''downloads the audio from a YouTube video and saves it as an mp3 file. The progess_hook callback sends sse status messagees.'''
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
        send_sse_message("server-error", "YouTube download failed.")
        raise DownloadException("YouTube download failed.") from e


# progress_hook must remain synchronous.
def progress_hook(d):
    status = d.get('status')

    if status == 'finished' or status == 'downloading':
        # e.g.: _default_template = '100% of    2.42MiB'
        pct_download = f"Downloaded: {d.get('_default_template')}"
        send_sse_message("status", pct_download)
    elif status == 'error':
        # TODO
        # There are different error numbers we could provide
        # more info.  It would take a bit to get that sorted out. So for another time.
        send_sse_message("server-error", 'Error downloading YouTube audio.')
        pass

def sanitize_title(youtube_title: str) -> str:
    # Remove invalid characters
    filename = re.sub(r'[\\/*?:"<>|]', "", youtube_title)
    # Remove leading/trailing white space
    filename = filename.strip()
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    return filename