import asyncio
import logging
import os
import time

from pydub import AudioSegment
import torch
from transformers import pipeline

from global_stuff import global_message_queue
from logger_code import LoggerBase
from transcription_state_code import TranscriptionState
from utils import msg_log


logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

# This is for storing the temporary audio slice when the audio is divided into chapters.
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

class TranscribeAudio:
    def __init__(self):
        pass

    async def transcribe_chapters(self, state: TranscriptionState, logger: LoggerBase):
        # As the transcription progresses, the sequence of communication - both status updates and results are placed on the message queue to be delivered to the client.
        asyncio.create_task(global_message_queue.put({'status': f'Transcribing {len(state.chapters)} chapter(s).'}))
        # Send the filename w/o extension to the client. This becomes the name of the obsidian note.
        start_time = time.time()
        asyncio.create_task(global_message_queue.put({'filename': os.path.splitext(os.path.basename(state.local_mp3))[0]}))
        transcribe_tasks = [asyncio.create_task(self.transcribe_chapter(state.local_mp3, state.hf_model, state.hf_compute_type, chapter, logger)) for chapter in state.chapters]

        await asyncio.gather(*transcribe_tasks)
        end_time = time.time()
        duration = end_time - start_time
        state.transcription_time = duration
        asyncio.create_task(global_message_queue.put("data", {'transcription_time': duration} ))
        msg_log("status", "All chapters successfully transcribed.", f"All chapters successfully transcribed. Transcription time: {duration} seconds First Chapter: {state.chapters[0]}", logger)
        logger.debug(f"transcription_code.TranscribeAudio.transcribe_chapters: All chapters transcribed. Transcription time: {duration} First Chapter: {state.chapters[0]}")

    async def transcribe_chapter(self, local_mp3:str, model_name:str, compute_type:str, chapter:str, logger: LoggerBase):
        # Make audio slice
        audio_slice = self.make_audio_slice(local_mp3, chapter.start*1000, chapter.end*1000 )
        # # Load model
        transcriber = pipeline("automatic-speech-recognition",
                           model=model_name,
                           device=0 if torch.cuda.is_available() else -1,
                           torch_dtype=compute_type)

        # Transcribe
        result = transcriber(audio_slice, chunk_length_s=30, batch_size=8)

        # Delete audio slice from chapters
        if audio_slice != local_mp3:
            os.remove(audio_slice)

        chapter =  result['text']

        # asyncio.create_task(send_message("transcription", {'chapter': chapter}, logger))


    def make_audio_slice(self, local_mp3:str, start_ms:int, end_ms:int):
        if end_ms == 0: # The audio is not divided into chapters
            return local_mp3
        audio = AudioSegment.from_file(local_mp3)
        audio_segment = audio[start_ms:end_ms]
        temp_audio_path = os.path.join(f'{LOCAL_DIRECTORY}', f"temp_{start_ms}_{end_ms}.wav")
        audio_segment.export(temp_audio_path, format="wav")
        return temp_audio_path