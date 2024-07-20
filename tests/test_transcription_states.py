
import logging
import pytest
from pydantic import ValidationError
from audio_processing_model import AudioProcessRequest, COMPUTE_TYPE_MAP
from exceptions_code import KeyException
from transcription_state_code import TranscriptionStates, TranscriptionState, Chapter, build_chapters
from logger_code import LoggerBase

@pytest.fixture
def logger():
    return LoggerBase.setup_logger(__name__, logging.DEBUG)

@pytest.fixture
def transcription_states():
    return TranscriptionStates()

@pytest.mark.parametrize("youtube_url, audio_file, audio_quality, expected_key", [
    ("https://www.youtube.com/watch?v=bckD_GK80oY", None, "high", "https://www.youtube.com/watch?v=bckD_GK80oY_default"),# There is no "high" audio quality. It would be "large".  Thus, "default" is used by the code.
    (None, "/path/to/audiofile.m4a", "medium", "audiofile_medium"),
    (None, None, "default", None),  # Code isn't being given an audio source to process.
    ("https://youtube.com/somevideo", "/path/to/audiofile.mp3", "large", None), # YouTube video is invalid
    (None,"c:\\Users\\happy\\Documents\\Projects\\obsidian-transcriber-service\\local\\Patreon_book_club_Leon_Hussey.m4a","default","Patreon_book_club_Leon_Hussey_default"),
])

def test_make_key(youtube_url, audio_file, audio_quality, expected_key):
    # audio_input = AudioProcessRequest(youtube_url=youtube_url, audio_file=audio_file, audio_quality=audio_quality)
    # ts = TranscriptionStates()
    # if expected_key is None:
    #     with pytest.raises(KeyException):
    #         key = ts.make_key(audio_input)
    #     return
    # key = ts.make_key(audio_input)
    # assert key == expected_key
    try:
        audio_input = AudioProcessRequest(youtube_url=youtube_url, audio_file=audio_file, audio_quality=audio_quality)
        ts = TranscriptionStates()

        key = ts.make_key(audio_input)
        assert key == expected_key, f"Expected key: {expected_key}, but got: {key}"

    except (KeyException, ValidationError) as e:
        assert expected_key is None, f"Unexpected error: {e}"

@pytest.mark.parametrize("key, state, should_raise, expected_message", [
    ("test_key", TranscriptionState(basename="the_audio_file_basename"), False, "transcripts_state_code.TranscriptionStates.add_state: test_key added to cache."),
    ("test_key", "invalid_state", True, "transcription_state must be an instance of TranscriptionState.")
])
def test_add_state(mocker, transcription_states, key, state, should_raise, expected_message):
    mock_logger = mocker.patch('transcription_state_code.logger', autospec=True)
    if should_raise:
        with pytest.raises(ValueError, match=expected_message):
            transcription_states.add_state(key, state, mock_logger)
    else:
        transcription_states.add_state(key, state, mock_logger)
        assert transcription_states.cache[key] == state
        mock_logger.debug.assert_called_once_with(expected_message)

@pytest.mark.parametrize("key, state, expected_result", [
    ("existing_key", TranscriptionState(basename="the_audio_file_basename"), True),
    ("non_existing_key", None, False)
])
def test_get_state(transcription_states, key, state, expected_result):
    if state:
        transcription_states.cache[key] = state

    result = transcription_states.get_state(key)
    if expected_result:
        assert result == state, f"Expected state: {state}, but got: {result}"
    else:
        assert result is None, f"Expected None, but got: {result}"

@pytest.mark.parametrize("chapter_dicts, expected_chapters", [
    (
        [
            {"title": "Chapter 1", "start_time": 0.0, "end_time": 0.0},
            {"title": "Chapter 2", "start_time": 0.0, "end_time": 0.0}
        ],
        [
            Chapter(title="Chapter 1", start_time=0.0, end_time=0.0),
            Chapter(title="Chapter 2", start_time=0.0, end_time=0.0)
        ]
    ),
    (
        [
            {"title": "Chapter 1", "start_time": 0.0}  # Missing end_time
        ],
        (TypeError, ValidationError)
    ),
    (
        [
            {"title": "Chapter 1", "start_time": "00:00:00", "end_time": 1000}  # end_time should be a string
        ],

        (TypeError, ValidationError)
    )
])
def test_build_chapters(chapter_dicts, expected_chapters):
    if isinstance(expected_chapters, list):
        print("chapter_dicts: ", chapter_dicts)
        result = build_chapters(chapter_dicts)
        assert result == expected_chapters
    else:
        with pytest.raises(expected_chapters):
            print(f"Raised exception: {expected_chapters}")
            build_chapters(chapter_dicts)

import pytest
from transcription_state_code import TranscriptionState, Metadata, Chapter

@pytest.mark.parametrize("basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected_exception", [
    (
        "test_file_1",
        "/path/to/audio1.mp3",
        "model1",
        "compute_type1",
        Metadata(download_time=100),
        [Chapter(title="Chapter 1", start_time=0.0, end_time=600.0)],
        ValidationError # The hf_compute_type must be a dtype.
    ),
    (
        "test_file_2",
        "/path/to/audio2.mp3",
        "model2",
        COMPUTE_TYPE_MAP['default'],
        Metadata(download_time=200),
        [Chapter(title="Chapter 1", start_time=0.0, end_time=600.0), Chapter(title="Chapter 2", start_time=600.0, end_time=1200.0)],
        None # The start_time must be a float.
    ),
    (
        None,  # Invalid basename
        "/path/to/audio3.mp3",
        "model3",
        COMPUTE_TYPE_MAP['default'],
        Metadata(download_time=300),
        [Chapter(title="Chapter 1", start_time=0.0, end_time=600.0)],
        ValidationError
    )
])
def test_transcription_state_creation(basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected_exception):
    if expected_exception is None:
        state = TranscriptionState(
            basename=basename,
            local_audio_path=local_audio_path,
            hf_model=hf_model,
            hf_compute_type=hf_compute_type,
            metadata=metadata,
            chapters=chapters
        )
        assert state is not None
    else:
        with pytest.raises(expected_exception):
            TranscriptionState(
                basename=basename,
                local_audio_path=local_audio_path,
                hf_model=hf_model,
                hf_compute_type=hf_compute_type,
                metadata=metadata,
                chapters=chapters
            )

@pytest.mark.parametrize("key, basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected", [
    ("key1", "basename1", "path1", "model1", COMPUTE_TYPE_MAP['default'], Metadata(download_time=100), [Chapter(title="Chapter 2", start_time=0.0, end_time=0.0,transcript="transcript")], True),
    ("key1", "basename1", None, None, COMPUTE_TYPE_MAP['default'], Metadata(download_time=100), [Chapter(title="Chapter 2", start_time=0.0, end_time=0.0,transcript="transcript")], True), #
    ("key1", "basename1", "path1", "model1", COMPUTE_TYPE_MAP['default'], Metadata(download_time=100), [], False),

])
def test_is_complete(key, basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected):
    state = TranscriptionState(key=key, basename=basename, local_audio_path=local_audio_path, hf_model=hf_model, hf_compute_type=hf_compute_type, metadata=metadata, chapters=chapters)
    assert state.is_complete() == expected
