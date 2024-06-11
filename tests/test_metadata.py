'''The tests in this file explore creation of a Metadata Pydantic class.
The first, simple_metadata_building, creates a Metadata instance from a hand crafted dictionary.
The second, building_youtube_metadata, creates a Metadata instance from a dictionary extracted from a YouTube video.
The third, building_mp3_metadata, creates a Metadata instance from a dictionary extracted from an mp3 audio file.
'''
import json
import logging
import os


from dotenv import load_dotenv
load_dotenv()
import pytest
# The actual name of the directory/folder holding file writes
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY")

from audio_processing_model import AudioProcessRequest
from logger_code import LoggerBase
from metadata_code import MetadataExtractor, Metadata

logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)

audio_input_youtube = AudioProcessRequest(youtube_url="https://www.youtube.com/watch?v=KbZDsrs5roI", audio_quality="default")

@pytest.fixture
def test_info_dict():
    test_info_dict = "test_info_dict_KbZDsrs5roI.json"
    return test_info_dict

def load_youtube_info_dict(filename):
    filepath = f"{LOCAL_DIRECTORY}/{filename}"
    with open(filepath) as f:
        info_dict = json.load(f)
    return info_dict



def test_simple_metadata_building():

    metadata_instance = Metadata(
        filename="example.mp4",
        tags=["tag1, tag2, tag3"],
        description="This is an example video",
        duration="00:10:00",
        upload_date="2022-01-01",
        chapters_metadata=[]
    )
    return metadata_instance

def test_building_youtube_metadata(test_info_dict):
    info_dict = load_youtube_info_dict(test_info_dict)
    extractor = MetadataExtractor()
    metadata = extractor.build_metadata_instance(info_dict)
    print(metadata)
    return metadata

def test_building_mp3_metadata():
    extractor = MetadataExtractor()
    mp3_filepath = f"{LOCAL_DIRECTORY}/Teaming_with_microbes_chapter_14.mp3"
    info_dict = extractor.build_mp3_info_dict(mp3_filepath=mp3_filepath)
    metadata = extractor.build_metadata_instance(  info_dict)
    return metadata
#===================================
dashes = '\n' + '-' * 45 + '\n'
logger.debug(f'{dashes}Test 1: simple metadata building.  A dict is hand crufted and then converted to a Metadata instance.{dashes}')
metadata = test_simple_metadata_building()
logger.debug(f"simple metadata: {metadata.model_dump_json(indent=2)}")

logger.debug(f'{dashes}Test 2: info_dict from YouTube video plus some additonal properties are put into a Metadata instance.{dashes}')
metadata = test_building_youtube_metadata("test_info_dict_KbZDsrs5roI.json")
logger.debug(f"youTube metadata: {metadata.model_dump_json(indent=2)}")

logger.debug(f'{dashes}Test 3: info_dict from mp3 audio plus some additonal properties are put into a Metadata instance.{dashes}')
metadata = test_building_mp3_metadata()
logger.debug(f"mp 3 metadata: {metadata.model_dump_json(indent=2)}")
