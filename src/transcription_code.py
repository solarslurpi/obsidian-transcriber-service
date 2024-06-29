import asyncio
import logging
import os


from pydub import AudioSegment
import torch

from exceptions_code import TranscriberException
from logger_code import LoggerBase
from transformers import pipeline
from transcription_state_code import TranscriptionState


logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

# This is for storing the temporary audio slice when the audio is divided into chapters.
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

class TranscribeAudio:
    def __init__(self):
        pass

    async def transcribe_chapters(self, state: TranscriptionState):
        transcribe_tasks = [asyncio.create_task(self.transcribe_chapter(local_mp3=state.local_mp3,
                                                                        model_name=state.hf_model,
                                                                        compute_type=state.hf_compute_type, start_time=chapter.start_time, end_time=chapter.end_time)) for chapter in state.chapters]

        texts = await asyncio.gather(*transcribe_tasks)
        chapter_number = 1
        for chapter, text in zip(state.chapters, texts):
            chapter.transcript = text
            chapter.number = chapter_number
            chapter_number += 1

        logger.debug(f"transcription_code.TranscribeAudio.transcribe_chapters: All chapters transcribed. ")

    async def transcribe_chapter(self, local_mp3:str, model_name:str, compute_type:torch.dtype, start_time:int, end_time:int):
        try:
            audio_slice = self.make_audio_slice(local_mp3, start_time*1000, end_time*1000 )
            # # # Load model
            transcriber = pipeline("automatic-speech-recognition",
                            model=model_name,
                            device=0 if torch.cuda.is_available() else -1,
                            torch_dtype=compute_type)

            # # Transcribe
            result = transcriber(audio_slice, chunk_length_s=30, batch_size=8)
        except Exception as e:
            logger.error(f"transcription_code.TranscribeAudio.transcribe_chapter: Error {e}.")
            raise TranscriberException("Error transcribing chapter")

        # # Delete audio slice from chapters
        if audio_slice != local_mp3:
            os.remove(audio_slice)

        chapter =  result['text']

        return chapter

    def make_audio_slice(self, local_mp3:str, start_ms:int, end_ms:int):
        if end_ms == 0: # The audio is not divided into chapters
            return local_mp3
        audio = AudioSegment.from_file(local_mp3)
        audio_segment = audio[start_ms:end_ms]
        temp_audio_path = os.path.join(f'{LOCAL_DIRECTORY}', f"temp_{start_ms}_{end_ms}.wav")
        audio_segment.export(temp_audio_path, format="wav")
        return temp_audio_path