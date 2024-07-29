import io
import pytest
from fastapi import UploadFile
from audio_processing_model import AudioProcessRequest
@pytest.mark.parametrize(
    "youtube_url, upload_file, audio_quality, expected_error",
    [(None, UploadFile(filename="example.mp3",file=io.BytesIO(b"dummy content")), "default", None)]
)
def test_serialize_audio_processing_model(youtube_url, upload_file, audio_quality, expected_error):
    try:
        # Create an instance.
        audio_input = AudioProcessRequest(
            YouTube=youtube_url,
            upload_file=upload_file,
            audio_quality=audio_quality
        )
        #serialize.
        audio_input_dict = audio_input.model_dump()
        assert audio_input.youtube_url == youtube_url
        assert audio_input.upload_file == upload_file
        assert audio_input.audio_quality == audio_quality
    except ValueError as e:
        assert expected_error == ValueError
    else:
        if expected_error:
            pytest.fail("Expected an error but none was raised")