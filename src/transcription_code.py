import asyncio
import logging
import os


from pydub import AudioSegment
import psutil
import torch

from exceptions_code import TranscriberException
from logger_code import LoggerBase
from transcription_state_code import TranscriptionState, Chapter
from utils import send_sse_message
import whisper



logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

# This is for storing the temporary audio slice when the audio is divided into chapters.
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

class TranscribeAudio:
    def __init__(self, audio_quality:str):
        try:
            self.model = whisper.load_model(audio_quality)
            logger.debug(f"Model loaded. Size: {audio_quality}")
        except Exception as e:
            logger.error(f"Error loading model. {e}")
            send_sse_message("server-error", f"Error loading model. {e}")
            raise TranscriberException(f"Error loading model. {e}")

    async def transcribe_chapters(self, state: TranscriptionState):
        # Check if GPU is available
        if torch.cuda.is_available():
            device = 'GPU'
        else:
            device = 'CPU'
        logging.debug(f"Running on {device}")
        # Run monitor_system and transcribe_audio_slices concurrently
        # await asyncio.gather(
        #     self.monitor_system(),
        #     self.transcribe_audio_slices(state)
        # )
        state = await self.transcribe_audio_slices(state)
        return state

    async def transcribe_audio_slices(self, state: TranscriptionState):
        audio_slices = self.make_audio_slices(state)

        results_list = []
        length_audio_slices = len(audio_slices)
        await send_sse_message("status",f"Starting to transcribe {length_audio_slices} chapters.")
        for index, audio_slice in enumerate(audio_slices, start=1):
            try:
                # I started thinking breaking up the audio into chapters (when available in the metadata) would be a way to speed up the transcription process.  However, I found out the whisper model is not thread safe.
                # transcribe_tasks = [asyncio.create_task(self.transcribe_audio(audio = audio_slice, audio_quality=state.hf_model) ) for audio_slice in audio_slices]
                # results_list = await asyncio.gather(*transcribe_tasks)
                await send_sse_message("status",f"Transcribing chapter {index}/{length_audio_slices}")
                logger.debug(f"Transcribing chapter {index}/{length_audio_slices}")
                result = await self.transcribe_audio(audio = audio_slice, audio_quality=state.hf_model)

                results_list.append(result)
            except TranscriberException as e:
                raise e

        await send_sse_message("status","Transcription Complete. On to collecting and sending the results.")
        logging.debug("***Transcription Complete. On to collecting and sending the results.***")
        # Check if the transcription did not come with chapter metadata information.  Chapters exists,
        # however the end_time = 0.0 and the len of chapters is 1.
        if len(state.chapters) == 1:
            # Build Chapters based on the segments provided in the results dict.
            state.chapters = self.make_chapters(results_list[0])
        else: # Add the transcript text to each chapter.
            chapter_number = 1
            # The chapters were pulled out separately through concurrent extraction of the audio slices.
            # At this stage, the transcribed text and chapter number is added to each chapter.
            for chapter, results in zip(state.chapters, results_list):
                chapter.text = results['text']
                chapter.number = chapter_number
                chapter_number += 1

        logger.debug(f"transcription_code.TranscribeAudio.transcribe_chapters: All chapters transcribed. ")
        return state # The state is returned.  However it is a singleton.

    async def transcribe_audio(self, audio: str, audio_quality:str) -> str:
        # whisper is not thread safe.  It does not like to reuse a loaded model.
        logging.debug(f"--->Start Transcription for {audio}")
        result = self.model.transcribe(audio)
        logger.debug(f"<---Done transcribing {audio}.")
        return result


    async def monitor_system(self):
        try:
            # await asyncio.sleep(20) # Wait a bit for transcription to get under way
            # cpu_threshold, gpu_threshold = await self.determine_baseline(duration=6)
            # Keep It Simple until the system is better understood.
            cpu_threshold = 5.0
            gpu_threshold = 5.0
            # Monitor transcription progress and detect frozen state
            frozen_start_time = None
            frozen_threshold_seconds = 20 # If transcription has been inactive for this amount of time, it is considered frozen.
            while True:
                # Monitor CPU usage
                cpu_usage = psutil.cpu_percent(interval=1)
                logger.debug(f"CPU Usage: {cpu_usage}%")

                # Monitor GPU usage if available
                gpu_usage = None
                if torch.cuda.is_available():
                    gpu_usage = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
                    logger.debug(f"GPU Usage: {gpu_usage:.2f}%")
                # Check if the system is frozen
                if cpu_usage < cpu_threshold and (gpu_threshold is None or gpu_usage < gpu_threshold):
                    if frozen_start_time is None:
                        frozen_start_time = asyncio.get_event_loop().time()
                    elif asyncio.get_event_loop().time() - frozen_start_time > frozen_threshold_seconds:
                        logger.error("Transcription process is frozen based on low CPU/GPU usage.")
                        await send_sse_message("server-error", "Transcription process is frozen based on low CPU/GPU usage.")
                        raise TranscriberException("Transcription process is frozen based on low CPU/GPU usage.")
                else:
                    frozen_start_time = None
                # Let the system keep going.
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.debug("Monitoring task was cancelled.")

    def make_audio_slices(self, state: TranscriptionState):
        # Initialize the audio slices
        audio_slices = []
        if state.chapters is None:
            raise ValueError("Cannot Continue transcribing. The state information does not include chapters.")
        if state.local_audio_path is None or not os.path.exists(state.local_audio_path):
            raise FileNotFoundError("Cannot Continue transcribing. The state information does not include a valid audio file.")
        if state.chapters[0].end_time == 0: # The audio is not divided into chapters
            audio_slices.append(state.local_audio_path)
            return audio_slices
        audio_segments = AudioSegment.from_file(state.local_audio_path)
        # chapters contains chapter objects
        for chapter in state.chapters:
            audio_segment = audio_segments[chapter.start_time*1000:chapter.end_time*1000]
            temp_audio_path =  os.path.join(f'{LOCAL_DIRECTORY}', f"temp_{chapter.start_time}_{chapter.end_time}.wav")
            audio_segment.export(temp_audio_path, format="wav")
            audio_slices.append(temp_audio_path)
        return audio_slices

    def make_chapters(self, results, time_length:float =120.0):
        '''Whisper results can be one long line of characters.  This is difficult for clients like Obsidian to handle.  By using the segment information that is returned in the results, we can chunk transcripts that do not have chapter info (so far the only one this code has seen are YouTube chapters) into manageable chapters.  Unlike YouTube chapters, these chapters are only based on time and not the content of the discussion.'''
        try:
            segments = results['segments']
        except KeyError as e:
            logger.error(f"transcription_code.TranscribeAudio.make_chapters: Error {e}.")
            raise
        chapters = []
        current_chunk = {
            'start_time': segments[0]['start'],
            'end_time': segments[0]['end'],
            'text': segments[0]['text']
        }

        current_duration = segments[0]['end'] - segments[0]['start']
        current_chapter = 1
        # Step 4: Iterate over the segments
        for segment in segments[1:]: # This will cover all the text that was transcribed.
            segment_duration = segment['end'] - segment['start']
            # The transcript is broken into time_length chapters (say 2 minutes for example).
            # Until time_length is reached given the segment times, the text is added to the chunk which then becomes a Chapter.
            if current_duration + segment_duration <= time_length:
                current_chunk['end_time'] = segment['end']
                current_chunk['text'] += ' ' + segment['text']
                current_duration += segment_duration
            else:
                # Have the time_length text and start/stop times.  Create a chapter.
                chapter = Chapter(title=' ', start_time=current_chunk['start_time'], end_time=current_chunk['end_time'], text=current_chunk['text'],number=current_chapter)
                chapters.append(chapter)
                current_chapter += 1
                # onto the next chapter
                current_chunk = {
                    'start_time': segment['start'],
                    'end_time': segment['end'],
                    'text': segment['text']
                }

                current_duration = segment_duration

        # Add any remaining chunk
        if current_chunk:
            chapter = Chapter(title=' ', start_time=current_chunk['start_time'], end_time=current_chunk['end_time'], text=current_chunk['text'],number=current_chapter)
            chapters.append(chapter)

        return chapters

    async def determine_baseline(self,duration=10):
        cpu_usages = []
        gpu_usages = []
        for _ in range(duration):
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_usages.append(cpu_usage)
            if torch.cuda.is_available():
                gpu_usage = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
                gpu_usages.append(gpu_usage)

            await asyncio.sleep(1)
        cpu_threshold = sum(cpu_usages) / len(cpu_usages) / 2
        gpu_threshold = sum(gpu_usages) / len(gpu_usages) / 2
        logger.debug(f"CPU Threshold: {cpu_threshold}, GPU Threshold: {gpu_threshold}")
        return cpu_threshold, gpu_threshold
