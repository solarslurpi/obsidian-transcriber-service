import json
import logging
import os
import pytest
import torch

from audio_processing_model import AudioProcessRequest, AUDIO_QUALITY_MAP, COMPUTE_TYPE_MAP
from exceptions_code import DownloadException, MetadataExtractionException
from metadata_extractor_code import MetadataExtractor
from process_check_code import process_check
from transcription_state_code import TranscriptionState


'''The test below was to better understand the Exception path if the exception happened at a lowest layer of the process_check function.  This one is for Metadata.  The initialize_transcription_state function is mocked to raise a MetadataExtractionException.  What was of greatest interest was understanding the cleanup process.'''

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")

# This is to be used to mask the actual metadata extraction process.  It is a mock of the metadata object.  By providing reliable metadata, a test can focus on other parts of the process.
async def get_metadata(audio_input):
    filepath = f"{LOCAL_DIRECTORY}/test_info_dict_KbZDsrs5roI.json"
    with open(filepath) as f:
        info_dict = json.load(f)
    extractor = MetadataExtractor()
    metadata = extractor.build_metadata_instance(info_dict)
    return metadata

def build_state(metadata):
    state = TranscriptionState(local_mp3=None, audio_quality='default', metadata=metadata, hf_model="openai/whisper-tiny.en", hf_compute_type=torch.float16)
    return state

@pytest.fixture
def youtube_url():
    return "https://www.youtube.com/watch?v=KbZDsrs5roI"

def faulty_download_youtube(youtube_url=youtube_url, base_filename="bluelab_pulse_meter"):
    print("-> faulty_download_youtube.")
    raise DownloadException("download_failed")


# Custom function to simulate MetadataExtractionException
async def faulty_initialize_transcription_state(audio_input):
    raise MetadataExtractionException("Metadata extraction failed")

async def mock_initialize_transcription_state(audio_input):
    metadata = await get_metadata(audio_input)
    state = build_state(metadata)
    return state


@pytest.mark.asyncio
async def test_monkeying():
    m = MetadataExtractor()
    m.extract_metadata = get_metadata
    metadata = await m.extract_metadata("test")
    print(m)

    # Patch
# @pytest.mark.asyncio
# async def test_process_check_metadata_extraction_exception(mocker, caplog, youtube_url):
#     audio_input = AudioProcessRequest(youtube_url=youtube_url, audio_quality="default")

#     # Patch the initialize_transcription_state with the custom faulty function
#     mocker.patch("process_check_code.initialize_transcription_state", side_effect=faulty_initialize_transcription_state)

#     # Capture log records
#     with caplog.at_level(logging.DEBUG):
#         await process_check(audio_input)

#    # Print out all log messages
#     for record in caplog.records:
#         print(f"{record.levelname}: {record.message}")
#     # Check if the log contains the expected error message
#     assert any(
#         "handle_exception: Metadata extraction failed" in record.message
#         for record in caplog.records
#     )
#---------------
@pytest.mark.asyncio
async def test_process_check_youtube_download_exception(mocker, caplog, youtube_url):

    audio_input = AudioProcessRequest(youtube_url=youtube_url, audio_quality="default")

    # Patch the initialize_transcription_state with the custom test function.
    mocker.patch("process_check_code.initialize_transcription_state", side_effect=mock_initialize_transcription_state)
    # Patch the youtube_download with the custom faulty function.
    mocker.patch("process_check_code.youtube_download", side_effect=faulty_download_youtube)

    # Capture log records
    with caplog.at_level(logging.DEBUG):
        raised = False
        try:
            await process_check(audio_input)
        except DownloadException as e:
            print(f"\n**>DownloadException:<** {e}\n\n")
            raised = True

   # Print out all log messages
    for record in caplog.records:
        print(f"{record.levelname}: {record.message}")
    # Check if the log contains the expected error message
    assert raised, "Expected DownloadException to be raised."
#---------------
# Add the below code to run pytest when this script is executed directly
if __name__ == "__main__":
    pytest.main([__file__])
