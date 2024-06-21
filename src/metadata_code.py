
import logging
import os
import re
from datetime import datetime
from typing import Optional

from mutagen.mp3 import MP3
from typing import Annotated, Tuple, Dict, List
import yt_dlp
from pydantic import BaseModel, Field, PlainSerializer, field_validator

from dotenv import load_dotenv
load_dotenv()

from exceptions_code import MetadataExtractionException
from logger_code import LoggerBase
from utils import send_sse_message, mock_info_dict, mock_chapters

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

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
    download_time: Optional[int] = Field(default=None, description="Number of seconds it took to download the YouTube Video.")
    transcription_time: Optional[int] = Field(default=None, description="Number of seconds it took to transcribe a 'chapter' of an audio file.")

    @field_validator('duration')
    def validate_duration(cls,v):
        if not re.match(r'^\d+:\d+:\d+$', v):
            raise ValueError(f"Invalid duration format: {v}. Expected format: hh:mm:ss")
        return v

class MetadataExtractor:
    '''
    Objective: Extract rich metadata from YouTube videos and MP3 files to enhance transcription searchability.

    Process:
    1. Extract metadata into `info_dict`.
    2. Use `info_dict` to create a `Metadata` instance.
    3. Use `info_dict` to create a list of chapters.
    3. Include `Metadata` and chapters from `info_dict` in `TranscriptionState`.

    Note: Chapters are used directly in `TranscriptionState` but not in `Metadata`.
    '''

    def __init__(self):
        pass

    def extract_youtube_metadata(self, youtube_url: str):
        '''The metadata is extracted before downloading. Maybe we don't have to. could be one download and then transcribe chapters. TBD.  Download is all at once. Transcriptions are per chapter.'''
        logger.debug(f"metadata_code.extract_youtube_metadata: Extracting metadata for {youtube_url}")
        ydl_opts = {
            'outtmpl': '%(title)s',
            'quiet': True,
            'simulate': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # TEST:
                # metadata, chapters = self.extract_youtube_metadata_and_chapter_dicts(ydl_opts)
                info_dict = ydl.extract_info(youtube_url, download=False)
                metadata = self.build_metadata_instance(info_dict)
                # extract chapters if present
                chapter_dicts = info_dict.get('chapters', [])
        except Exception as e:
            logger.error(f"Failed to extract metadata for {youtube_url}: {e}")
            raise e
        return metadata, chapter_dicts

    def extract_youtube_metadata_and_chapter_dicts(self, ydl_opts: dict) -> Tuple[Dict, List]:
        # Extract the metadata and chapters info from the YouTube metadata into info_dict {} using the youtubeDownload function in
        # youtube_download_code.py.  The metadata is just downloaded, not the audio file. That comes afterwards.
        info_dict = mock_info_dict()
        chapter_dicts = mock_chapters(info_dict)
        metadata = self.build_metadata_instance(info_dict)
        return metadata, chapter_dicts

    def extract_mp3_metadata_and_chapter_dicts(self, mp3_file) -> Metadata:
        info_dict, chapters = self.build_mp3_info_dict_and_chapter_dicts(mp3_file)
        metadata= self.build_metadata_instance(info_dict)
        return metadata, chapters

    def build_mp3_info_dict_and_chapter_dicts(self, mp3_filepath: str) -> Tuple[Dict, List]:
        audio = MP3(mp3_filepath)
        duration = round(audio.info.length)
        upload_date = datetime.fromtimestamp(os.path.getmtime(mp3_filepath)).strftime('%Y-%m-%d')
        title = os.path.basename(mp3_filepath).replace('_', ' ').rsplit('.', 1)[0]

        info_dict = {
            "duration": duration,
            "upload_date": upload_date,
            "title": title,
        }
        chapter_dicts =  [{'title': '', 'start': 0, 'end': 0}]
        # mp3 files aren't broken into chapters. They are considered to have one chapter.
        # setting the end to 0.0 tells the system that the audio is not divided into chapters.

        return info_dict, chapter_dicts

    def build_metadata_instance(self, info_dict: Dict) -> Metadata:
        # Convert duration and chapters
        info_dict['duration'] = self.format_time(info_dict.get('duration', 0))
        return Metadata(**info_dict)

    def format_time(self, seconds: int) -> str:
        if not isinstance(seconds, int):
            return "0:00:00"
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:d}:{mins:02d}:{secs:02d}"


    async def extract_metadata_and_chapter_dicts(self, audio_input ) -> Metadata:
        logger.debug("metadata_code.extract_metadata: Getting the metadata.")
        # When creating, add in what the client has given us into the state instance.
        if audio_input.youtube_url:
            # Instantiate a new state with all the info we can.
            try:
                # Second status sent to the client if need to extract metadata.
                send_sse_message(event="status", data="Metadata extraction started.")
                metadata, chapter_dicts  = self.extract_youtube_metadata(youtube_url=audio_input.youtube_url)


            except Exception as e:
                raise MetadataExtractionException("Error extracting metadata") from e

        else:
            try:
                # Should be quick turn around so not sending sse messages.
                logger.debug(f"metadata_code.extract_metadata: Extracting metadata for {audio_input.mp3_file}")
                metadata, chapter_dicts = self.extract_mp3_metadata_and_chapter_dicts(mp3_file=audio_input.mp3_file )
            except Exception as e:
                raise MetadataExtractionException("Error extracting metadata") from e
        return metadata, chapter_dicts