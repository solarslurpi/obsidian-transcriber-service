import os
import glob
import pytest

from audio_handler_code import AudioHandler
from audio_processing_model import AudioProcessRequest
from metadata_shared_code import Metadata


@pytest.fixture
def mock_audio_file():
    return 'tests/audio_files/test_audio_file.m4a'
@pytest.fixture
def audio_handler(mock_audio_file, audio_file=None, ):
    if not audio_file:
        audio_file = mock_audio_file
    # Create an AudioProcessRequest instance with the audio file
    audio_request = AudioProcessRequest(audio_file=audio_file)
    # Return an AudioHandler instance with the audio request
    return AudioHandler(audio_request)

@pytest.fixture
def chapter_dicts():
    return [{'title': '', 'start_time': 0.0, 'end_time': 0.0}]

@pytest.fixture
def info_dict():
    return {"title": "test"}

def get_audio_files(directory):
    # Use a generator to yield audio files in the specified directory
    for file_path in glob.iglob(os.path.join(directory, '*')):
        if os.path.isfile(file_path):
            yield file_path

@pytest.mark.parametrize("audio_file", list(get_audio_files('tests/audio_files')))
def test_build_audio_info_dict_and_chapter_dicts(audio_handler, audio_file):
    audio_info_dict, chapter_dicts = audio_handler._build_audio_info_dict_and_chapter_dicts(audio_file)

    # Print the keys of the audio metadata dictionary
    for key, value in audio_info_dict.items():
        print(f"Metadata for {audio_file} - {key}: {value}")

    assert isinstance(audio_info_dict, dict), "Audio metadata should be a dictionary"
    assert isinstance(chapter_dicts, list), "Chapter dicts should be a list"
    assert "title" in audio_info_dict, "Audio metadata should contain a title"
    assert "upload_date" in audio_info_dict, "Audio metadata should contain an upload date"
    assert len(chapter_dicts) > 0, "Chapter dicts should not be empty"
    assert "start_time" in chapter_dicts[0], "Chapter dicts should contain start_time"
    assert "end_time" in chapter_dicts[0], "Chapter dicts should contain end_time"

@pytest.mark.asyncio
async def test_extract(mocker, info_dict, chapter_dicts, audio_handler):
    # Mock the _build_audio_info_dict_and_chapter_dicts method
    mock_build_audio_info_dict_and_chapter_dicts = mocker.patch(
        'audio_handler_code.AudioHandler._build_audio_info_dict_and_chapter_dicts',
        return_value=(info_dict, chapter_dicts)
    )

    # Call the extract method
    audio_info_dict, chapter_dicts, audio_file = await audio_handler.extract()

    # Assertions
    mock_build_audio_info_dict_and_chapter_dicts.assert_called_once_with("tests/audio_files/test_audio_file.m4a")

    assert audio_info_dict['title'] == "test"
    assert len(chapter_dicts) > 0
    assert audio_file == "tests/audio_files/test_audio_file.m4a"

def test_extract_audio_attributes():
    audio_handler = AudioHandler(AudioProcessRequest(audio_file='tests/audio_files/test.mp3'))
    audio_attributes = audio_handler._extract_audio_attributes('tests/audio_files/test.mp3')