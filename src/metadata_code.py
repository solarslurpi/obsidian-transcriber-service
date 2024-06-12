
import logging
import os
from datetime import datetime
from typing import Optional

from mutagen.mp3 import MP3
from typing import Annotated, Dict, List
import yt_dlp
from pydantic import BaseModel, Field, PlainSerializer

from dotenv import load_dotenv
load_dotenv()

from exceptions_code import MetadataExtractionException
from logger_code import LoggerBase
from utils import cleaned_name, MsgLog, send_sse_message

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class ChapterMetadata(BaseModel):
    title: Optional[str] = Field(default='', description="Title of the chapter.")
    start: int = Field(..., description="Start time of the chapter in seconds.")
    end: int = Field(..., description="End time of the chapter in seconds.")

CustomStr = Annotated[
    List, PlainSerializer(lambda x: ' '.join(x), return_type=str)
]
class Metadata(BaseModel):
    youtube_url: Optional[str] = Field(default=None, alias="original_url", description="URL of the YouTube video.")
    title: str = Field(default=None, description="Title field as it is in index_dict.  It will be the YouTube title or the basefilename of the mp3 file.")
    tags: Optional[CustomStr] = Field(default=None, description="Tags associated with the metadata. The CustomStr annotation is used to convert the list of tags provided by YouTube to a string.")
    description: Optional[str] = Field(default=None, description="Description associated with the metadata.")
    duration: Optional[str] = Field(default=None, description="Duration of the audio in hh:mm:ss.")
    channel: Optional[str] = Field(default=None, description="channel name")
    upload_date: Optional[str]
    uploader_id: Optional[str] = Field(default=None, description="uploader id")
    chapters_metadata: List[ChapterMetadata]

class MetadataExtractor:
    def __init__(self):
        pass

    def extract_youtube_metadata(self, youtube_url: str):
        logger.debug(f"metadata_code.extract_youtube_metadata: Extracting metadata for {youtube_url}")
        ydl_opts = {
            'outtmpl': '%(title)s',
            'quiet': True,
            'simulate': True,
            'getfilename': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            metadata = self.build_metadata_instance( info_dict)


        return metadata

    def extract_mp3_metadata(self, mp3_file, audio_quality: str) -> Metadata:
        info_dict = self.build_mp3_info_dict(mp3_file)
        metadata = self.build_metadata_instance(info_dict)
        return metadata

    def build_mp3_info_dict(self, mp3_filepath: str) -> Dict:
        audio = MP3(mp3_filepath)
        duration = round(audio.info.length)
        upload_date = datetime.fromtimestamp(os.path.getmtime(mp3_filepath)).strftime('%Y-%m-%d')
        title=os.path.basename(mp3_filepath)

        info_dict = {
            "duration": duration,
            "upload_date": upload_date,
            "title": title,
        }
        # mp3 files aren't broken into chapters. They are considered to have one chapter.
        # setting the end to 0.0 tells the system that the audio is not divided into chapters.

        return info_dict

    def build_metadata_instance(self, info_dict: Dict) -> Metadata:
        # Include additional metadata fields if youtube.\


        # Convert duration and chapters
        info_dict['duration'] = self.format_time(info_dict.get('duration', 0))
        info_dict['chapters_metadata'] = [
            ChapterMetadata(title=chap.get('title', ''), start=chap['start_time'], end=chap['end_time'])
            for chap in info_dict.get('chapters', [{'start_time': 0.0, 'end_time': 0.0}])
        ]

        return Metadata(**info_dict)


    def format_time(self, seconds: int) -> str:
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:d}:{mins:02d}:{secs:02d}"


    async def extract_metadata(self, audio_input ) -> Metadata:
        logger.debug("metadata_code.extract_metadata: Getting the metadata.")
        # When creating, add in what the client has given us into the state instance.
        if audio_input.youtube_url:
            # Instantiate a new state with all the info we can.
            try:
                send_sse_message(event="status", data="Extracted Metadata.")
                metadata  = self.extract_youtube_metadata(youtube_url=audio_input.youtube_url)
                send_sse_message(event="status", data="Metadata extracted.")

            except Exception as e:
                raise MetadataExtractionException("Error extracting metadata") from e

        else:
            try:
                # Should be quick turn around so not sending sse messages.
                logger.debug(f"metadata_code.extract_metadata: Extracting metadata for {audio_input.mp3_file}")
                metadata = self.extract_mp3_metadata(mp3_file=audio_input.mp3_file, audio_quality=audio_input.audio_quality)
            except Exception as e:
                raise MetadataExtractionException("Error extracting metadata") from e
        return metadata