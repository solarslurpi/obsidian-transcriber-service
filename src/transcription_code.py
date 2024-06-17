import asyncio
import logging
import os
import time

from pydub import AudioSegment
import torch

from logger_code import LoggerBase
from transcription_state_code import TranscriptionState, ChapterTranscript
from utils import send_sse_message


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
        # As the transcription progresses, the sequence of communication - both status updates and results are placed on the message queue to be delivered to the client.
        send_sse_message("data", {'num_chapters': len(state.chapters)})

        start_time = time.time()
        transcribe_tasks = [asyncio.create_task(self.transcribe_chapter(state.local_mp3, state.hf_model, state.hf_compute_type, chapter)) for chapter in state.chapters]

        texts = await asyncio.gather(*transcribe_tasks)
        cnt = 1
        for chapter, text in zip(state.chapters, texts):
            chapter.transcript = text + f" {cnt}"
            chapter_dict = chapter.model_dump()
            send_sse_message("data", {'chapter': chapter_dict, 'number': cnt})
            cnt += 1

        end_time = time.time()
        duration = end_time - start_time
        state.transcription_time = duration
        send_sse_message("data", {'transcription_time': duration})

        logger.debug(f"transcription_code.TranscribeAudio.transcribe_chapters: All chapters transcribed. Transcription time: {duration} First Chapter: {state.chapters[0]}")

    async def transcribe_chapter(self, local_mp3:str, model_name:str, compute_type:torch.dtype, chapter:ChapterTranscript):
        # Make audio slice
        # c = chapter.chapter_metadata
        # audio_slice = self.make_audio_slice(local_mp3, c.start*1000, c.end*1000 )
        # # # Load model
        # transcriber = pipeline("automatic-speech-recognition",
        #                    model=model_name,
        #                    device=0 if torch.cuda.is_available() else -1,
        #                    torch_dtype=compute_type)

        # # Transcribe
        # result = transcriber(audio_slice, chunk_length_s=30, batch_size=8)

        # # Delete audio slice from chapters
        # if audio_slice != local_mp3:
        #     os.remove(audio_slice)

        # chapter =  result['text']
        chapter = "This is a test transcription"

        return chapter

        # asyncio.create_task(send_message("transcription", {'chapter': chapter}, logger))


    def make_audio_slice(self, local_mp3:str, start_ms:int, end_ms:int):
        if end_ms == 0: # The audio is not divided into chapters
            return local_mp3
        audio = AudioSegment.from_file(local_mp3)
        audio_segment = audio[start_ms:end_ms]
        temp_audio_path = os.path.join(f'{LOCAL_DIRECTORY}', f"temp_{start_ms}_{end_ms}.wav")
        audio_segment.export(temp_audio_path, format="wav")
        return temp_audio_path