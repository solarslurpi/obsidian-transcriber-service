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
    transcribe_audio = TranscribeAudio()
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

@pytest.mark.asyncio
async def test_transcribe_chapters_flow(mocker):
    transcribe_audio = TranscribeAudio()
    mocker.patch.object(TranscribeAudio,'transcribe_audio', return_value=results[0])
    await transcribe_audio.transcribe_chapters(state=transcription_state_one_chapter)

def test_chapters_model_dump():
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

@pytest.mark.asyncio
async def test_transcribe_one_chapter_transcript(transcription_state_one_chapter):
    transcribe_audio = TranscribeAudio()
    # Actually do the transcription
    state = await transcribe_audio.transcribe_chapters(state=transcription_state_one_chapter)
    # Write the state to a file so it can be loaded and populated in a new run
    with open('tests/state.json', 'w') as file:
        json.dump(state.model_dump(), file, indent=4)
    # Check that there is at least one chapter
    assert len(state.chapters) > 0, "No chapters were created."

    # Check each chapter has all attributes
    for chapter in state.chapters:
        assert chapter.title is not None, "Chapter title is None."
        assert chapter.number is not None, "Chapter number is None."
        assert chapter.start_time is not None, "Chapter start time is None."
        assert chapter.end_time is not None, "Chapter end time is None."
        assert chapter.text is not None, "Chapter text is None."
        assert chapter.text != "", "Chapter text is empty."

@pytest.mark.asyncio
async def test_transcribe_multiple_chapter_transcript(transcription_state_multiple_chapters):
    transcribe_audio = TranscribeAudio()
    # Actually do the transcription
    state = await transcribe_audio.transcribe_chapters(state=transcription_state_multiple_chapters)
