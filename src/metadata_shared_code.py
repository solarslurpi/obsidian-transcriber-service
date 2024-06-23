import os
from typing import Dict, List, Optional, Annotated
from pydantic import BaseModel, Field, PlainSerializer

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

CustomStr = Annotated[List, PlainSerializer(lambda x: ' '.join(x), return_type=str)]

class Metadata(BaseModel):
    youtube_url: Optional[str] = Field(default=None, alias="original_url", description="URL of the YouTube video.")
    title: str = Field(default=None, description="Title field as it is in index_dict. It will be the YouTube title or the basefilename of the mp3 file.")
    tags: Optional[CustomStr] = Field(default=None, description="Tags associated with the metadata. The CustomStr annotation is used to convert the list of tags provided by YouTube to a string.")
    description: Optional[str] = Field(default=None, description="Description associated with the metadata.")
    duration: Optional[str] = Field(default=None, description="Duration of the audio in hh:mm:ss.")
    channel: Optional[str] = Field(default=None, description="channel name")
    upload_date: Optional[str]
    uploader_id: Optional[str] = Field(default=None, description="uploader id")
    download_time: Optional[int] = Field(default=None, description="Number of seconds it took to download the YouTube Video.")
    transcription_time: Optional[int] = Field(default=None, description="Number of seconds it took to transcribe a 'chapter' of an audio file.")

class MetadataMixin:
    def build_metadata_instance(self, info_dict: Dict) -> Metadata:
        info_dict['duration'] = self._format_time(info_dict.get('duration', 0))
        return Metadata(**info_dict)

    def _format_time(self, seconds: int) -> str:
        if not isinstance(seconds, int):
            return "0:00:00"
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:d}:{mins:02d}:{secs:02d}"
