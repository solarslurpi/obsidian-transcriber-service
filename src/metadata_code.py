# metadata_service.py
import re

from mutagen.mp3 import MP3
from typing import Dict
import yt_dlp

import os
from datetime import datetime

from logger_code import LoggerBase
from pydantic_models import global_state, AUDIO_QUALITY_MAP, COMPUTE_TYPE_MAP

class MetadataService:
    def extract_youtube_metadata(self, youtube_url: str) -> None:
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
            metadata = {
                "youTube URL": info_dict.get('webpage_url', ''),
                "filename": sanitized_filename,
                "tags": formatted_tags,
                "description": info_dict.get('description', ''),
                "duration": self.format_time(info_dict.get('duration', 0)),
                "audio quality": AUDIO_QUALITY_MAP.get(global_state.audio_quality, ''),
                "channel name": info_dict.get('uploader', ''),
                "upload date": info_dict.get('upload_date', ''),
                "uploader id": info_dict.get('uploader_id', '')
            }
            return metadata


    def extract_mp3_metadata(self, mp3_filepath: str) -> Dict[str, str]:
        audio = MP3(mp3_filepath)
        duration = round(audio.info.length)
        upload_date = datetime.fromtimestamp(os.path.getmtime(mp3_filepath)).strftime('%Y-%m-%d')
        basefilename=os.path.basename(mp3_filepath)
        global_state.update(basefilename=basefilename)
        return {
            "duration": self.format_time(duration),
            "upload_date": upload_date,
            "filename": basefilename,
            "audio quality": AUDIO_QUALITY_MAP.get(global_state.audio_quality, ''),
        }

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