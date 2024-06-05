import json
import logging
import re
import os
from datetime import datetime
from typing import Optional

from mutagen.mp3 import MP3
from typing import Dict, List, Tuple
import yt_dlp
from pydantic import BaseModel, Field


from logger_code import LoggerBase
from audio_processing_model import  AUDIO_QUALITY_MAP, AudioProcessRequest
from utils import cleaned_name



logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class ChapterWithoutTranscript(BaseModel):
    title: Optional[str] = Field(default='', description="Title of the chapter.")
    start: int = Field(..., description="Start time of the chapter in seconds.")
    end: int = Field(..., description="End time of the chapter in seconds.")

class Metadata(BaseModel):
    youTube_URL: str = Field(default=None, alias="youTube URL")
    filename: str = Field(..., description="Name of the mp3 file.")
    tags: Optional[str] = Field(default=None, description="Tags associated with the metadata.")
    description: Optional[str] = Field(default=None, description="Description associated with the metadata.")
    duration: Optional[str] = Field(default=None, description="Duration of the audio in hh:mm:ss.")
    audio_quality: Optional[str] = Field(default=None, alias="audio quality")
    channel_name: Optional[str] = Field(default=None, alias="channel name")
    upload_date: Optional[str]
    uploader_id: Optional[str] = Field(default=None, alias="uploader id")
    chapters: List[ChapterWithoutTranscript]

class MetadataExtractor:
    def __init__(self):
        pass

    def extract_youtube_metadata(self, youtube_url: str, audio_quality:str):
        logger.debug(f"metadata_code.extract_youtube_metadata: Extracting metadata for {youtube_url}")
        ydl_opts = {
            'outtmpl': '%(title)s',
            'quiet': True,
            'simulate': True,
            'getfilename': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            filename = ydl.prepare_filename(info_dict)
            metadata = self.build_metadata_instance(filename, info_dict, audio_quality)

            return metadata

    def build_mp3_info_dict(self, mp3_filepath: str) -> Dict:
        audio = MP3(mp3_filepath)
        duration = round(audio.info.length)
        upload_date = datetime.fromtimestamp(os.path.getmtime(mp3_filepath)).strftime('%Y-%m-%d')
        basefilename=os.path.basename(mp3_filepath)

        info_dict = {
            "duration": duration,
            "upload_date": upload_date,
            "filename": basefilename,
            "chapters": [{'start_time': 0.0, 'end_time': 0.0}],
        }
        # mp3 files aren't broken into chapters. They are considered to have one chapter.
        # setting the end to 0.0 tells the system that the audio is not divided into chapters.

        return info_dict

    def build_metadata_instance(self, filename, info_dict: Dict, audio_quality: str) -> Metadata:

        audio_quality_value = AUDIO_QUALITY_MAP.get(audio_quality, '')
        if not audio_quality_value:
            raise ValueError("Invalid audio quality provided")

        # Sanitize filename
        sanitized_filename = self.sanitize_filename(filename)
        info_dict['filename'] = sanitized_filename
        info_dict['audio_quality'] = audio_quality_value
        info_dict['duration'] = self.format_time(info_dict.get('duration', 0))
        info_dict['chapters'] = [
            ChapterWithoutTranscript(title=chap.get('title', ''), start=chap['start_time'], end=chap['end_time'])
            for chap in info_dict.get('chapters', [{'start_time': 0.0, 'end_time': 0.0}])
        ]

        return Metadata(**info_dict)


    def format_time(self, seconds: int) -> str:
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:d}:{mins:02d}:{secs:02d}"

    def sanitize_filename(self, filename: str) -> str:
        # Remove the file extension
        name_part = filename.rsplit('.', 1)[0]

        # Replace full-width colons and standard colons with a hyphen or other safe character
        name_part = name_part.replace('：', '_').replace(':', '_')
        # Replace spaces with hyphens
        safe_filename = cleaned_name(name_part)

        return safe_filename

    def extract_metadata(self, audio_input: AudioProcessRequest) -> Tuple[Dict, List]:
        logger.debug("metadata_code.extract_metadata: Getting the metadata.")
        # When creating, add in what the client has given us into the state instance.
        if audio_input.youtube_url:
            # Instantiate a new state with all the info we can.
            try:
                metadata, chapters = self.extract_youtube_metadata(youtube_url=audio_input.youtube_url, audio_quality=audio_input.audio_quality)
            except Exception as e:
                logger.error(f"metadata_code.initialize_transcription_state:Error extracting YouTube metadata: {e}")
                raise Exception(f"metadata_code.initialize_transcription_state: Failed to extract YouTube metadata for URL {audio_input.youtube_url}: {e}")
        else:
            try:
                metadata = self.extract_mp3_metadata(mp3_filepath=audio_input.local_mp3, audio_quality=audio_input.audio_quality)
            except Exception as e:
                logger.error(f"metadata_code.initialize_transcription_state:Error extracting YouTube metadata: {e}")
                raise Exception(f"metadata_code.initialize_transcription_state: Failed to extract YouTube metadata for URL {audio_input.youtube_url}: {e}")
        return metadata