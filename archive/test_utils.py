import io
import json
import logging
import os

from fastapi import UploadFile
import requests
import pytest


from dotenv import load_dotenv
load_dotenv()

from audio_processing_model import AudioProcessRequest
from logger_code import LoggerBase
from metadata_extractor_code import Metadata, MetadataExtractor, ChapterMetadata

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

@pytest.fixture
def upload_file():
    if not hasattr(upload_file,"-cache"):
        filepath = f"{LOCAL_DIRECTORY}/Bluelab_Pulse_Meter_Review.mp3"
        with open(filepath, "rb") as f:
            file_content = f.read()
        file_like = io.BytesIO(file_content)
        file_like.filename = os.path.basename(filepath)
        upload_file._cache = UploadFile(filename=os.path.basename(filepath), file=file_like)

@pytest.fixture
def info_dict():
    if not hasattr(info_dict, "_cache"):
        filepath = f"{LOCAL_DIRECTORY}/test_info_dict_KbZDsrs5roI.json"
        with open(filepath) as f:
            info_dict._cache = json.load(f)
            # Convert duration and chapters
            info_dict._cache['duration'] = str(info_dict._cache['duration'])
            info_dict._cache['chapters_metadata'] = [
                ChapterMetadata(title=chap.get('title', ''), start=chap['start_time'], end=chap['end_time'])
            for chap in info_dict._cache.get('chapters', [{'start_time': 0.0, 'end_time': 0.0}])
        ]

    return info_dict._cache

@pytest.fixture
def mock_metadata(info_dict):
    if not hasattr(mock_metadata, "_cache"):
        mock_metadata._cache = Metadata(**info_dict)
    return mock_metadata._cache

@pytest.fixture
def logger():
    logger = LoggerBase.setup_logger(__name__, level=logging.DEBUG)
    return logger

@pytest.fixture
def audio_input():
    mp3_local = f"{LOCAL_DIRECTORY}/Bluelab_Pulse_Meter_Review.mp3"
    audio_input = AudioProcessRequest(mp3_local=mp3_local)

    return audio_input


def test_post_to_process_mp3(logger):
    url = "http://127.0.0.1:8000/api/v1/process_audio"
    payload = {'youtube_url': 'junk_url', 'audio_quality': 'default'}
    headers = {'accept': 'application/json'}
    logger.debug('before post')
    response = requests.post(url, headers=headers, data=payload)
    logger.debug('after post')
    return response

# It is a mock of the metadata object.  By providing reliable metadata, a test can focus on other parts of the process.
async def mock_extract_metadata(info_dict):
    # audio_input is not used because the metadata originated from a file.
    logger.debug(f"info_dict: {json.dumps(info_dict, indent=4)}")
    extractor = MetadataExtractor()
    metadata = extractor.build_metadata_instance(info_dict)
    return metadata