import json
import pytest
from transcription_code import TranscribeAudio
from transcription_state_code import TranscriptionState, Chapter
import json

@pytest.fixture
def transcribe_audio_mock(mocker, results):
    transcribe_audio_mock = mocker.patch('transcription_code.TranscribeAudio.transcribe_audio', return_value=results)
    return transcribe_audio_mock
@pytest.fixture
def results():
    with open('tests/results.json') as file:
        results = json.load(file)
    return results

@pytest.fixture
def transcription_state_one_chapter():
    return TranscriptionState(
        key="test_key",
        hf_model="tiny.en",
        basename="test_basename",
        local_audio_path= r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\audio_files\test.mp3",
        chapters=[Chapter(start_time=0.0, end_time=0.0)]
    )
@pytest.fixture
def transcription_state_multiple_chapters():
    with open('tests/chapters.json') as file:
        chapters_dict = json.load(file)
        chapters = [Chapter(**chapter) for chapter in chapters_dict]

    return TranscriptionState(
        key="test_key",
        basename="test_basename",
        local_audio_path= r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\audio_files\test.mp3",
        chapters=chapters
    )

def test_make_chapters(results):
    '''
    Use stored results to test the make_chapters method.
    '''
    transcribe_audio = TranscribeAudio("tiny")
    chapters = transcribe_audio.make_chapters(results[0])
    assert len(chapters) > 0
    # Check each chapter has all attributes
    for chapter in chapters:
        assert chapter.title is not None, "Chapter title is None."
        assert chapter.number is not None, "Chapter number is None."
        assert chapter.start_time is not None, "Chapter start time is None."
        assert chapter.end_time is not None, "Chapter end time is None."
        assert chapter.text is not None, "Chapter text is None."
        assert chapter.text != "", "Chapter text is empty."

def test_chapters_model_dump():
    # model_dump() is a Pydantic 2 method that returns a dictionary.  It gets confusing because Pydantic models can have attributes that are not serializable.  A Pydantic class might have to use @field_serializer to convert an attribute to a serializable type.  This is a simple test on a Pydantic class that is easily serializable but helps better understand the model_dump() method.
    chapters = [Chapter(title="test", number=1, start_time=0.0, end_time=0.0, text="test text")]
    chapters_dict = [chapter.model_dump() for chapter in chapters]
    assert chapters_dict[0]['title'] == "test"
    assert chapters_dict[0]['number'] == 1
    assert chapters_dict[0]['start_time'] == 0.0
    assert chapters_dict[0]['end_time'] == 0.0
    assert chapters_dict[0]['text'] == "test text"

def test_chapter_model_dump():
    chapter = Chapter(title="test", number=1, start_time=0.0, end_time=0.0, text="test text")
    chapter_dict = chapter.model_dump()
    assert chapter_dict['title'] == "test"
    assert chapter_dict['number'] == 1
    assert chapter_dict['start_time'] == 0.0
    assert chapter_dict['end_time'] == 0.0
    assert chapter_dict['text'] == "test text"
