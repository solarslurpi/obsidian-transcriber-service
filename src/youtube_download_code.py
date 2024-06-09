import asyncio

import yt_dlp

from logger_code import LoggerBase
from audio_processing_model import AudioProcessRequest
from transcription_state_code import TranscriptionState



class YouTubeDownloader:
    def __init__(self, state:TranscriptionState, logger: LoggerBase):
        self.logger = logger
        self.state = state

    async def download_audio(self, youtube_url:str, base_filename:str):
        self.logger.debug(f"Downloading audio from {youtube_url}")
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, self.download_yt_to_mp3(youtube_url, base_filename))


    # yt_dlp is a synchronous wrapper around youtube-dl. The progress_hook is synchronous.
    def download_yt_to_mp3(self, youtube_url:str, base_filename:str, ):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': base_filename ,
            'progress_hooks': [self.progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'postprocessor_args': [
                '-ac', '1', # Convert to mono
                '-ar', '44100' # Set sampling rate to 44.1 kHz
            ]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])


    # progress_hook must remain synchronous.
    def progress_hook(self, d):
        status = d.get('status')
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        if status == 'finished':
            # asyncio.run_coroutine_threadsafe(send_message('status', "Download finished successfully.", self.logger), loop)
            self.isComplete = True
        elif status == 'downloading':
            downloaded = d.get('downloaded_bytes')
            total = d.get('total_bytes')
            if total:
                percentage = downloaded / total * 100
                # asyncio.run_coroutine_threadsafe(send_message('status', f"Downloading: {percentage:.1f}%", self.logger), loop)
        elif status == 'error':
            # asyncio.run_coroutine_threadsafe(send_message('error', f"An error occurred: {d.get('error', 'Unknown error')}", self.logger), loop)
            self.isComplete = True

    def  is_youtube_url(request: AudioProcessRequest) -> bool:
        if request.youtube_url and request.file:
            raise ValueError("Please provide either a YouTube URL or an MP3 file, not both.")
        elif request.youtube_url:
            return True
        elif request.file:
            return False
        else:
            raise ValueError("No YouTube URL or file provided.")
