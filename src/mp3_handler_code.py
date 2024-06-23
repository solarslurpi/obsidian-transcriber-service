import os
from datetime import datetime
from typing import List, Tuple, Dict
from mutagen.mp3 import MP3
from metadata_shared_code import MetadataMixin, Metadata

class MP3Handler(MetadataMixin):
    def __init__(self, audio_input):
        self.audio_input = audio_input

    async def extract(self) -> Tuple[Metadata, List, str]:
        info_dict, chapters = self._build_mp3_info_dict_and_chapter_dicts(self.audio_input.mp3_file)
        metadata= self.build_metadata_instance(info_dict)
        return metadata, chapters, self.audio_input.mp3_file

    def _build_mp3_info_dict_and_chapter_dicts(self, mp3_filepath: str) -> Tuple[Dict, List]:
        audio = MP3(mp3_filepath)
        duration = round(audio.info.length)
        upload_date = datetime.fromtimestamp(os.path.getmtime(mp3_filepath)).strftime('%Y-%m-%d')
        title = os.path.basename(mp3_filepath).replace('_', ' ').rsplit('.', 1)[0]

        info_dict = {
            "duration": duration,
            "upload_date": upload_date,
            "title": title,
        }
        # The format of a chapter comes from the format used by YouTube chapters.
        chapter_dicts =  [{'title': '', 'start_time': 0.0, 'end_time': 0.0}]
        # mp3 files aren't broken into chapters. They are considered to have one chapter.
        # setting the end to 0.0 tells the system that the audio is not divided into chapters.

        return info_dict, chapter_dicts