import logging
from dotenv import load_dotenv
load_dotenv()

from audio_processing_model import AudioProcessRequest
from logger_code import LoggerBase
from transcription_state_code import   initialize_transcription_state, states

logger = LoggerBase.setup_logger(__name__, level=logging.DEBUG)

# The transcription state holds all the information needed to transcribe a video.  We will test the various interactions to the state.

# The first interaction is determining if the state for this audio file already exists.

audio_input_youtube = AudioProcessRequest(youtube_url="https://www.youtube.com/watch?v=KbZDsrs5roI", audio_quality="default")

def test_if_state_exists():

    key = states.make_key(audio_input_youtube)
    logger.debug(f"state key is: {key}")

    state = states.get_state(key)
    if state:
    # The wind is at this audio's back...
        logger.debug("state is alredy in the cache.")
        logger.debug(f"{state.model_dump_json(indent=4)}")
    else:
        logger.debug("transcripts_state_code.initialize_transcription_state: state is not in the cache. ")



def main():
    dashes = '\n' + '-' * 45 + '\n'
    # logger.debug(f'{dashes}Test 1: Test if there are transcribed components already in a TranscriptState cache.{dashes}')
    # test_if_state_exists()
    logger.debug(f'{dashes}Test 2: Create an instance of a Transcription State.  INPUT = YOUTUBE URL.{dashes}')
    state = initialize_transcription_state(audio_input_youtube)
    logger.debug(f"transcripts_state: {state.model_dump_json(indent=4)}"  )

if __name__ == "__main__":
    main()
