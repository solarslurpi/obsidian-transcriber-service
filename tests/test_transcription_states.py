'''The TranscriptionStates Pydantic class is responsible for managing/maintaining the cache of transcriptions that have already been processed. This is to avoid reprocessing the same audio files.  Current features include:
- making a key to identify which audio file + audio quality has been processed.
- getting a state in the states cache based on the key.
- adding a state to the cache.
- loading the available states from disk.
- saving states to disk.
- NOT DONE: Removing states as the state cache grows too large.

Note: state include metadata, transcribed chapters, as well as the audio file path.

TO THE USER: If a transcription stops in the middle or completes, the state is saved. If a request comes in to transcribe the same audio file (or same YouTube URL from which the audio file is derived), the transcription process will make use of the state to continue or complete the transcription.
'''
import json
import logging
import os
import pytest
from pydantic import ValidationError
from audio_processing_model import AudioProcessRequest, COMPUTE_TYPE_MAP
from exceptions_code import KeyException
from transcription_state_code import TranscriptionStatesSingleton, TranscriptionState, Chapter, build_chapters
from logger_code import LoggerBase
import random

# Probably delete, but I liked this for now.
def random_state():
    states = TranscriptionStatesSingleton().get_states()
    random_index = random.randint(0, len(states.cache) - 1)
    print(f"list of keys: {list(states.cache.keys())}")
    print(f"specific key: {list(states.cache.keys())[random_index]}")
    state = states.get_state(list(states.cache.keys())[random_index])
    return state


@pytest.fixture
def states_singleton_no_store():
    # Setting load_from_store to False means the states will not be loaded from a file.  This way, we can test load_states() separately.
    return TranscriptionStatesSingleton().get_states(load_from_store=False)

@pytest.fixture
def key():
    return "https://www.youtube.com/shorts/0rvxUNga68g_tiny"

@pytest.fixture
def state():
    with open('tests/data/test_state_cache_one_complete.json', 'r') as f:
        state_dict = json.load(f)
    state = TranscriptionState(**state_dict)
    return state

@pytest.fixture
def logger():
    return LoggerBase.setup_logger(__name__, logging.DEBUG)

@pytest.mark.parametrize("youtube_url, audio_file, audio_quality, expected_key", [
    ("https://www.youtube.com/watch?v=bckD_GK80oY", None, "high", "https://www.youtube.com/watch?v=bckD_GK80oY_default"),# There is no "high" audio quality. It would be "large".  Thus, "default" is used by the code.
    (None, "/path/to/audiofile.m4a", "medium", "audiofile_medium"),
    (None, None, "default", None),  # Code isn't being given an audio source to process.
    ("https://youtube.com/somevideo", "/path/to/audiofile.mp3", "large", None), # YouTube video is invalid
    (None,"c:\\Users\\happy\\Documents\\Projects\\obsidian-transcriber-service\\local\\Patreon_book_club_Leon_Hussey.m4a","default","Patreon_book_club_Leon_Hussey_default"),
])

def test_make_key(youtube_url, audio_file, audio_quality, expected_key, states_singleton_no_store):
    # The key is used to identify a stored state in the cache (memory or on disk).  It is made up of the audio input component (YouTube URL or audio file) and the audio quality.  This test uses parametrize to test valid and invalid inputs for key creation.
    try:
        # Validate the audio input through the AudioProcessRequest Pydantic model.
        audio_input = AudioProcessRequest(youtube_url=youtube_url, audio_file=audio_file, audio_quality=audio_quality)
        # The make_key method is a method of the TranscriptionStates Pydantic model.
        ts = states_singleton_no_store # No need to load states from store for this test.
        # Call the method with the various parametrized inputs.
        key = ts.make_key(audio_input)
        # Check the assertions.
        assert key == expected_key, f"Expected key: {expected_key}, but got: {key}"

    except (KeyException, ValidationError) as e:
        assert expected_key is None, f"Unexpected error: {e}"

def test_load_states_empty_file(states_singleton_no_store):
    # To access the load_states method, use the singleton instance of TranscriptionStates.
    states = states_singleton_no_store # Since we're testing load_states, we don't want to access it through get_states() which calls load_states.
    states.state_file = 'tests/data/test_state_cache_empty.json'
    # State gets loaded from the 'state_cache/state_cache.json' file and added to the list of TranscriptionStates.
    # In order to test that the state_cache.json is empty and this doesn't break anything, a state_cache/test_state_cache_empty.json file is used.
    assert states.load_states()  == False, "Expected False, but got True."

# There are two phases in the transcription process: 1. Process input (YouTube URL or UploadFile) 2. Take input and transcribe.  The state is saved after each phase.
def test_load_states_local_audio_available(states_singleton_no_store, key):
    states = states_singleton_no_store
    states.state_file = 'tests/data/test_state_cache_with_audio_section.json'
    success = states.load_states()
    assert success == True, "Expected True, but got False."
    assert key in states.cache, f"Key '{key}' not found in states.cache"
    assert len(states.cache[key].chapters) == 1, "Expected 1, but got {len(states.cache[key].chapters)}"
    # assert the audio file is available at the local audio file path in the state.
    assert os.path.exists (states.cache[key].local_audio_path), f"Expected {states.cache[key].local_audio_path} to exist, but it doesn't."

def test_load_states_text_included(states_singleton_no_store, key):
    # Both audio prep and transcription completed successfully.  The complete state is available in that case so that when states.get_key(key) is called, the state is returned.
    states = states_singleton_no_store
    states.state_file = 'tests/data/test_state_cache_one_complete.json'
    success = states.load_states()
    assert success == True, "Expected True, but got False."
    state = states.get_state(key)
    assert len(state.chapters[0].text) > 1, f"Expected text to be present, but got {state.chapters[0].text}"
    assert state.metadata.download_time > 0, f"Expected download_time to be greater than 0, but got {state.metadata.download_time}"
    assert state.chapters[0].number == 1, f"Expected 1, but got {state.chapters[0].number}"

def test_load_states_bad_format(states_singleton_no_store):
    # Test loading multiple states from the state cache file.
    states = states_singleton_no_store
    states.state_file = 'tests/data/test_state_cache_multi_bad.json'
    success = states.load_states()
    assert success == False, "The json is malformed. Expected False but got true."

def test_load_multiple(states_singleton_no_store):
    states = states_singleton_no_store
    states.state_file = 'tests/data/test_state_cache_multi.json'
    success = states.load_states()
    assert success == True, "Expected True, but got False."
    assert len(states.cache) > 1, f"Expected more than 1, but got {len(states.cache)}"



# @pytest.mark.parametrize("key, state, expected_result", [
#     ("existing_key", TranscriptionState(basename="the_audio_file_basename"), True),
#     ("non_existing_key", None, False)
# ])
# def test_get_state(transcription_states, key, state, expected_result):
#     if state:
#         transcription_states.cache[key] = state

#     result = transcription_states.get_state(key)
#     if expected_result:
#         assert result == state, f"Expected state: {state}, but got: {result}"
#     else:
#         assert result is None, f"Expected None, but got: {result}"

# @pytest.mark.parametrize("chapter_dicts, expected_chapters", [
#     (
#         [
#             {"title": "Chapter 1", "start_time": 0.0, "end_time": 0.0},
#             {"title": "Chapter 2", "start_time": 0.0, "end_time": 0.0}
#         ],
#         [
#             Chapter(title="Chapter 1", start_time=0.0, end_time=0.0),
#             Chapter(title="Chapter 2", start_time=0.0, end_time=0.0)
#         ]
#     ),
#     (
#         [
#             {"title": "Chapter 1", "start_time": 0.0}  # Missing end_time
#         ],
#         (TypeError, ValidationError)
#     ),
#     (
#         [
#             {"title": "Chapter 1", "start_time": "00:00:00", "end_time": 1000}  # end_time should be a string
#         ],

#         (TypeError, ValidationError)
#     )
# ])
# def test_build_chapters(chapter_dicts, expected_chapters):
#     if isinstance(expected_chapters, list):
#         print("chapter_dicts: ", chapter_dicts)
#         result = build_chapters(chapter_dicts)
#         assert result == expected_chapters
#     else:
#         with pytest.raises(expected_chapters):
#             print(f"Raised exception: {expected_chapters}")
#             build_chapters(chapter_dicts)

# import pytest
# from transcription_state_code import TranscriptionState, Metadata, Chapter

# @pytest.mark.parametrize("basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected_exception", [
#     (
#         "test_file_1",
#         "/path/to/audio1.mp3",
#         "model1",
#         "compute_type1",
#         Metadata(download_time=100),
#         [Chapter(title="Chapter 1", start_time=0.0, end_time=600.0)],
#         ValidationError # The hf_compute_type must be a dtype.
#     ),
#     (
#         "test_file_2",
#         "/path/to/audio2.mp3",
#         "model2",
#         COMPUTE_TYPE_MAP['default'],
#         Metadata(download_time=200),
#         [Chapter(title="Chapter 1", start_time=0.0, end_time=600.0), Chapter(title="Chapter 2", start_time=600.0, end_time=1200.0)],
#         None # The start_time must be a float.
#     ),
#     (
#         None,  # Invalid basename
#         "/path/to/audio3.mp3",
#         "model3",
#         COMPUTE_TYPE_MAP['default'],
#         Metadata(download_time=300),
#         [Chapter(title="Chapter 1", start_time=0.0, end_time=600.0)],
#         ValidationError
#     )
# ])
# def test_transcription_state_creation(basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected_exception):
#     if expected_exception is None:
#         state = TranscriptionState(
#             basename=basename,
#             local_audio_path=local_audio_path,
#             hf_model=hf_model,
#             hf_compute_type=hf_compute_type,
#             metadata=metadata,
#             chapters=chapters
#         )
#         assert state is not None
#     else:
#         with pytest.raises(expected_exception):
#             TranscriptionState(
#                 basename=basename,
#                 local_audio_path=local_audio_path,
#                 hf_model=hf_model,
#                 hf_compute_type=hf_compute_type,
#                 metadata=metadata,
#                 chapters=chapters
#             )

# @pytest.mark.parametrize("key, basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected", [
#     ("key1", "basename1", "path1", "model1", COMPUTE_TYPE_MAP['default'], Metadata(download_time=100), [Chapter(title="Chapter 2", start_time=0.0, end_time=0.0,transcript="transcript")], True),
#     ("key1", "basename1", None, None, COMPUTE_TYPE_MAP['default'], Metadata(download_time=100), [Chapter(title="Chapter 2", start_time=0.0, end_time=0.0,transcript="transcript")], True), #
#     ("key1", "basename1", "path1", "model1", COMPUTE_TYPE_MAP['default'], Metadata(download_time=100), [], False),

# ])
# def test_is_complete(key, basename, local_audio_path, hf_model, hf_compute_type, metadata, chapters, expected):
#     state = TranscriptionState(key=key, basename=basename, local_audio_path=local_audio_path, hf_model=hf_model, hf_compute_type=hf_compute_type, metadata=metadata, chapters=chapters)
#     assert state.is_complete() == expected