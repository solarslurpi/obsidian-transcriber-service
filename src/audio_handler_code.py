import os
from datetime import datetime
from typing import List, Tuple, Dict
from tinytag import TinyTag

from audio_processing_model import AudioProcessRequest
from logger_code import LoggerBase
from metadata_shared_code import MetadataMixin, Metadata

logger = LoggerBase.setup_logger(__name__)

class AudioHandler(MetadataMixin):
    def __init__(self, audio_input: AudioProcessRequest):
        self.audio_input = audio_input

    async def extract(self) -> Tuple[Metadata, List, str]:
        info_dict, chapters = self._build_audio_info_dict_and_chapter_dicts(self.audio_input.audio_file)
        metadata= self.build_metadata_instance(info_dict)
        return metadata, chapters, self.audio_input.audio_file

    def _build_audio_info_dict_and_chapter_dicts(self, audio_filepath: str) -> Tuple[Dict, List]:
        # Using the TinyTag library to extract metadata from the audio file.
        audio_info_dict = None
        audio_info_dict = self._extract_audio_attributes(audio_filepath)
        audio_info_dict["upload_date"] = datetime.fromtimestamp(os.path.getmtime(audio_filepath)).strftime('%Y-%m-%d')
        audio_info_dict["title"] = os.path.basename(audio_filepath).replace('_', ' ')
        # The format of a chapter comes from the format used by YouTube chapters.
        chapter_dicts =  [{'title': '', 'start_time': 0.0, 'end_time': 0.0}]
        # audio files do not have chapters, so we set the start and end times to 0.0.
        return audio_info_dict, chapter_dicts

    def _extract_audio_attributes(self,file_path: str) -> Dict:
        if not os.path.isfile(file_path):
            logger.debug(f"Trying to extract audio attributes.  File not found: {file_path} Returning empty Dict.")
            return {}

        tag = TinyTag.get(file_path)

        # Common attributes people usually want
        common_attributes = ["title", "artist", "album", "genre", "year", "duration", "bitrate", "samplerate", "filesize", "track", "disc", "composer", "comment", "filetype"]

        # Filter common attributes that are not None and exist
        filtered_attributes = {attr: getattr(tag, attr) for attr in common_attributes if hasattr(tag, attr) and getattr(tag, attr) is not None}

        return filtered_attributes