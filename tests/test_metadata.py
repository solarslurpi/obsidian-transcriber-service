import json
import logging
import os


from dotenv import load_dotenv
load_dotenv()
# The actual name of the directory/folder holding file writes
LOCAL = os.getenv("LOCAL_DIRECTORY")

from logger_code import LoggerBase
from metadata_code import MetadataExtractor, Metadata

we_are_here = os.getcwd() # e.g.: 'C:\\Users\\happy\\Documents\\Projects\\obsidian-transcriber-service'
LOCAL_DIRECTORY = f"{we_are_here}/{LOCAL}"

logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)

def get_info_dict(filename):
    filepath = f"{LOCAL_DIRECTORY}/{filename}"
    with open(filepath) as f:
        info_dict = json.load(f)
        # Convert tags to a string.
        if 'tags' in info_dict:
            info_dict['tags'] = ', '.join(info_dict['tags'])
    return info_dict



def test_simple_metadata_building():

    metadata_instance = Metadata(
        filename="example.mp4",
        tags="tag1, tag2, tag3",
        description="This is an example video",
        duration="00:10:00",
        upload_date="2022-01-01",
        chapters=[]
    )
    return metadata_instance

def test_building_youtube_metadata():
    info_dict = get_info_dict("test_info_dict_KbZDsrs5roI.json")
    extractor = MetadataExtractor()
    metadata = extractor.build_metadata_instance( "blupulse_test.mp3", info_dict, 'default')
    return metadata

def test_building_mp3_metadata():
    extractor = MetadataExtractor()
    mp3_filepath = f"{LOCAL_DIRECTORY}/Bluelab_Pulse_Meter_Review.mp3"
    info_dict = extractor.build_mp3_info_dict(mp3_filepath=mp3_filepath)
    metadata = extractor.build_metadata_instance( "Bluelab_Pulse_Meter_Review.mp3", info_dict, 'default')
    return metadata
logger.debug('\n---------------------------------------------\nTest 1: simple metadata building/n  A dict is hand crufted and then converted to a Metadata instance.')
metadata = test_simple_metadata_building()
logger.debug(f"simple metadata: {metadata.model_dump_json(indent=2)}")

logger.debug('\n---------------------------------------------\nTest 2: info_dict from YouTube video plus some additonal properties are put into a Metadata instance.')
metadata = test_building_youtube_metadata()
logger.debug(f"youTube metadata: {metadata.model_dump_json(indent=2)}")

logger.debug('\n---------------------------------------------\nTest 3: info_dict from mp3 audio plus some additonal properties are put into a Metadata instance.')
metadata = test_building_mp3_metadata()
logger.debug(f"mp 3 metadata: {metadata.model_dump_json(indent=2)}")
