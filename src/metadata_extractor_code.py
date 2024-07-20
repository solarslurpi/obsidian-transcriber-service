
import logging
import os
from exceptions_code import MetadataExtractionException
from logger_code import LoggerBase
from audio_handler_code import AudioHandler
from youtube_handler_code import YouTubeHandler
from utils import send_sse_message
from dotenv import load_dotenv

load_dotenv()
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class MetadataExtractor:
    async def extract_metadata_and_chapter_dicts(self, audio_input):
        handler = self.get_handler(audio_input)
        try:
            metadata, chapter_dicts, audio_filepath = await handler.extract()
        except Exception as e:
            raise MetadataExtractionException("Error extracting metadata") from e
        return metadata, chapter_dicts, audio_filepath

    def get_handler(self, audio_input):
        if audio_input.youtube_url:
            return YouTubeHandler(audio_input)
        elif audio_input.audio_file:
            return AudioHandler(audio_input)
        else:
            raise AttributeError("audio_input does not have a supported attribute")
