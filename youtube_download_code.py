

from logger_code import LoggerBase


class YouTubeDownloader:
    def __init__(self, url:str, logger: LoggerBase):
        self.url = url
        self.logger = logger

    def download_audio(self):
        self.logger.debug(f"Downloading audio from {self.url}")
        pass
