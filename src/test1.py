from functools import partial
import asyncio
import re
import yt_dlp
import os
import logging

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
logger = logging.getLogger(__name__)

# Assuming global_message_queue is defined somewhere in your code
global_message_queue = asyncio.Queue()

def progress_hook(info_dict, queue, loop):
    if info_dict['status'] == 'finished' or info_dict['status'] == 'downloading':
        try:
            default_message = info_dict['_default_template']
            message = re.sub(r'\x1b\[.*?m', '', default_message)  # Remove ANSI escape sequences
            message = re.sub(r'\s+', ' ', message).strip()  # Replace multiple spaces with a single space
            print(message)
            asyncio.run_coroutine_threadsafe(queue.put(message), loop)
            if info_dict['status'] == 'finished':
                asyncio.run_coroutine_threadsafe(queue.put("done"), loop)
        except Exception as e:
            print(f'Error: {e}')
            raise e

def get_ydl_opts(queue, loop):
    yt_dlp_hook_partial = partial(progress_hook, queue, loop)

    ydl_opts = {
        'simulate': False,  # Download the audio file
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(LOCAL_DIRECTORY, '%(title)s.%(ext)s'),
        'quiet': True,
        'progress_hooks': [yt_dlp_hook_partial],  # Include the partial function here
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96',  # 96 kbps was chosen as a good balance between quality and file size for the audio text.
        }],
        'postprocessor_args': [  # Settings best for transcription
            '-ac', '1',  # Convert to mono
            '-ar', '44100'  # Set sampling rate to 44.1 kHz
        ],
    }

    return ydl_opts

async def download_video(youtube_url):
    loop = asyncio.get_running_loop()
    ydl_opts = get_ydl_opts(global_message_queue, loop)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            mp3_filepath = set_audio_input_path(info_dict.get('title', 'untitled'))
            metadata = build_metadata_instance(info_dict)
            chapter_dicts = info_dict.get('chapters', [])
    except Exception as e:
        logger.error(f"Failed to download video for {youtube_url}: {e}")
        raise e

    return metadata, chapter_dicts, mp3_filepath

def set_audio_input_path(title: str) -> str:
    yt_dlp_filename = title + ".mp3"
    mp3_filepath = os.path.join(LOCAL_DIRECTORY, yt_dlp_filename)
    return mp3_filepath

def build_metadata_instance(info_dict: dict) -> Metadata:
    info_dict['duration'] = format_time(info_dict.get('duration', 0))
    return Metadata(**info_dict)

def format_time(seconds: int) -> str:
    if not isinstance(seconds, int):
        return "0:00:00"
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:d}:{mins:02d}:{secs:02d}"
