import asyncio
import logging

from typing import Dict

from logger_code import LoggerBase
from transcription_state_code import TranscriptionState
logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

class TranscribeAudio:
    def __init__(self):
        pass

    async def transcribe_chapters(self, state: TranscriptionState, logger: LoggerBase):
        logger.debug(f"transcription_code.TranscribeAudio.transcribe_chapters: Transcribing chapters for {state}")
        transcribe_tasks = [asyncio.create_task(self.transcribe_chapter(chapter, logger)) for chapter in state.chapters]
        updated_chapters = await asyncio.gather(*transcribe_tasks)
        return updated_chapters


    async def transcribe_chapter(self, chapter:Dict, logger: LoggerBase):
        pass