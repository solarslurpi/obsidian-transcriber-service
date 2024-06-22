# metadata_extractor.py
import logging
import os
from typing import Annotated, Tuple, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, PlainSerializer
from exceptions_code import MetadataExtractionException
from logger_code import LoggerBase
from utils import send_sse_message
import yt_dlp
from mutagen.mp3 import MP3

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class MetadataExtractor:
    def extract_metadata_and_chapters(self, audio_input):
        handler = self.get_handler(audio_input)
        try:
            send_sse_message(event="status", data="Metadata extraction started.")
            metadata, chapter_dicts = handler.extract()
        except Exception as e:
            raise MetadataExtractionException("Error extracting metadata") from e
        return metadata, chapter_dicts

    def get_handler(self, audio_input):
        handlers = {
            'youtube_url': YouTubeHandler,
            'mp3_file': MP3Handler,
        }
        for attr, Handler in handlers.items():
            if hasattr(audio_input, attr):
                return Handler(getattr(audio_input, attr))
        raise AttributeError("audio_input does not have a supported attribute")

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

class MetadataMixin:
    def build_metadata_instance(self, info_dict: Dict) -> Metadata:
        # Convert duration and chapters
        info_dict['duration'] = self._format_time(info_dict.get('duration', 0))
        return Metadata(**info_dict)

    def _format_time(self, seconds: int) -> str:
        if not isinstance(seconds, int):
            return "0:00:00"
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:d}:{mins:02d}:{secs:02d}"



class YouTubeHandler(MetadataMixin):
    def __init__(self, youtube_url):
        self.youtube_url = youtube_url

    def extract(self):
        """
        -------------------
        NOTE: PLEASE CHECK THE 'simulate'ATTRIBUTE IN THE YDL_OPTS DICTIONARY. IF FALSE, THE AUDIO FILE WILL BE DOWNLOADED.
        -------------------
        extract_youtube_metadata_and_audio uses yt_dlp to download metadata and audio from a YouTube video synchronously. The FFmpegExtractAudio postprocessor is configured to extract audio at 96 kbps, a compromise between audio quality and file size, suitable for text transcription. Audio is converted to mono, and the sampling rate is adjusted to 44.1 kHz, following recommendations from the Whisper transcription software. The progress_hook callback, invoked by yt_dlp, provides system-wide progress updates. The function returns a metadata instance built from the metadata returned by yt_dlp.  The chapters that might be in the yt_dlp metadata are separated out into a list of chapter_dicts.
        """
        def progress_hook(d):
            status = d.get('status')
            if status == 'finished' or status == 'downloading':
                # e.g.: _default_template = '100% of    2.42MiB'
                pct_download = f"Downloaded: {d.get('_default_template')}"
                send_sse_message("status", pct_download)
            elif status == 'error':
                # TODO
                # There are different error numbers we could provide
                # more info.  It would take a bit to get that sorted out. So for another time.
                send_sse_message("server-error", 'Error downloading YouTube audio.')
                pass
        logger.debug(f"metadata_code.extract_youtube_metadata: Extracting metadata for {self.youtube_url}")

        ydl_opts = {
            'simulate': False, # Download the audio file
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'progress_hooks': [progress_hook], # progess_hook will be called with status updates.
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '96', # 96 kbps was chosen as a good balance between quality and file size for the audio text.
            }],
            # The post processor args are settings best for (whisper) transcription.
            'postprocessor_args': [ # Settings best for transcription
                '-ac', '1', # Convert to mono
                '-ar', '44100' # Set sampling rate to 44.1 kHz
            ],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # TEST:
                # metadata, chapters = self.extract_youtube_metadata_and_chapter_dicts(ydl_opts)
                info_dict = ydl.extract_info(self.youtube_url, download=True)
                # set audio_input.mp3_file to the filepath of the downloaded audio file.  The transcription code assumes the audio file is  downloaded and the audio_input instance has the mp3_file attribute set.
                filename = self._set_audio_input_path(info_dict.get('title', 'untitled'))
                metadata = self.build_metadata_instance(info_dict)
                # extract chapters if present
                chapter_dicts = info_dict.get('chapters', [])
        except Exception as e:
            logger.error(f"Failed to extract metadata for {self.youtube_url}: {e}")
            raise e
        return metadata, chapter_dicts

    def _set_audio_input_path(self, title: str) -> str:


        # Remove invalid characters
        filename = re.sub(r'[\\/*?:"<>|]', "", title)
        # Remove leading/trailing white space
        filename = filename.strip()
        # Replace spaces with underscores
        filename = filename.replace(" ", "_")
        return filename + ".mp3"

class MP3Handler(MetadataMixin):
    def __init__(self, mp3_file):
        self.mp3_file = mp3_file

    def extract(self):
        info_dict, chapters = self._build_mp3_info_dict_and_chapter_dicts(self.mp3_file)
        metadata= self.build_metadata_instance(info_dict)
        return metadata, chapters

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
        chapter_dicts =  [{'title': '', 'start': 0, 'end': 0}]
        # mp3 files aren't broken into chapters. They are considered to have one chapter.
        # setting the end to 0.0 tells the system that the audio is not divided into chapters.

        return info_dict, chapter_dicts