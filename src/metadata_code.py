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



logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class Chapter(BaseModel):
    title: str = Field(..., description="Title of the chapter.")
    start: int = Field(..., description="Start time of the chapter in seconds.")
    end: int = Field(..., description="End time of the chapter in seconds.")
    transcription: Optional[str] = Field(None, description="Transcription for the chapter.")

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
            tags = info_dict.get('tags', [])
            formatted_tags = ', '.join(tag.replace(' ', '_') for tag in tags)
            filename =  ydl.prepare_filename(info_dict)
            sanitized_filename = self.sanitize_filename(filename)
            logger.debug(f"metadata_code.extract_youtube_metadata: Filename: {sanitized_filename}")
            metadata = {
                "youTube URL": info_dict.get('webpage_url', ''),
                "filename": sanitized_filename,
                "tags": formatted_tags,
                "description": info_dict.get('description', ''),
                "duration": self.format_time(info_dict.get('duration', 0)),
                "audio quality": AUDIO_QUALITY_MAP.get(audio_quality, ''),
                "channel name": info_dict.get('uploader', ''),
                "upload date": info_dict.get('upload_date', ''),
                "uploader id": info_dict.get('uploader_id', ''),
                "chapters": info_dict.get('chapters', [{'start_time': 0.0, 'end_time': 0.0, 'title': ''}])
            }
            chapters_info =   info_dict.get('chapters', [{'start_time': 0.0, 'end_time': 0.0, 'title': '', 'transcription': None}])
            chapters = [Chapter(title=chap['title'], start=chap['start_time'], end=chap['end_time'], transcription=chap.get('transcription')) for chap in chapters_info]
            return metadata, chapters

    def extract_mp3_metadata(self, mp3_filepath: str, audio_quality: str) :
        audio = MP3(mp3_filepath)
        duration = round(audio.info.length)
        upload_date = datetime.fromtimestamp(os.path.getmtime(mp3_filepath)).strftime('%Y-%m-%d')
        basefilename=os.path.basename(mp3_filepath)
        metadata =  {
            "duration": self.format_time(duration),
            "upload_date": upload_date,
            "filename": basefilename,
            "audio quality": AUDIO_QUALITY_MAP.get(audio_quality, ''),
        }
        # mp3 files aren't broken into chapters. They are considered to have one chapter.
        # setting the end to 0.0 tells the system that the audio is not divided into chapters.
        chapter = Chapter(title='', start=0.0, end=0.0, transcription='')
        return metadata, [chapter]

    def format_time(self, seconds: int) -> str:
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:d}:{mins:02d}:{secs:02d}"

    def sanitize_filename(self, filename: str) -> str:
        # Remove the file extension
        name_part = filename.rsplit('.', 1)[0]

        # Replace full-width colons and standard colons with a hyphen or other safe character
        name_part = name_part.replace('：', '_').replace(':', '_')
        # Replace unwanted characters with nothing or specific symbols
        # This regex replaces any non-alphanumeric, non-space, and non-dot characters with nothing
        cleaned_name = re.sub(r"[^a-zA-Z0-9 \.-]", "", name_part)
        # Replace spaces with hyphens
        safe_filename = cleaned_name.replace(" ", "_")

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
                metadata, chapters = self.extract_mp3_metadata(mp3_filepath=audio_input.local_mp3, audio_quality=audio_input.audio_quality)
            except Exception as e:
                logger.error(f"metadata_code.initialize_transcription_state:Error extracting YouTube metadata: {e}")
                raise Exception(f"metadata_code.initialize_transcription_state: Failed to extract YouTube metadata for URL {audio_input.youtube_url}: {e}")
        return metadata, chapters