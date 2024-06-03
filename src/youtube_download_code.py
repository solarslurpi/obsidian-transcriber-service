

from logger_code import LoggerBase
from audio_processing_model import AudioProcessRequest


class YouTubeDownloader:
    def __init__(self, url:str, logger: LoggerBase):
        self.url = url
        self.logger = logger

    def download_audio(self):
        self.logger.debug(f"Downloading audio from {self.url}")
        pass


    def  is_youtube_url(request: AudioProcessRequest) -> bool:
        if request.youtube_url and request.file:
            raise ValueError("Please provide either a YouTube URL or an MP3 file, not both.")
        elif request.youtube_url:
            return True
        elif request.file:
            return False
        else:
            raise ValueError("No YouTube URL or file provided.")
