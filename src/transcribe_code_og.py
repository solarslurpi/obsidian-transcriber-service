

import os
import time

from pydub import AudioSegment
import torch
from transformers import pipeline

from logger_code import LoggerBase
from pydantic_models import  global_state, AUDIO_QUALITY_MAP, COMPUTE_TYPE_MAP
from process_update_manager_code import ProcessUpdateManager


async def transcribe_mp3(local_mp3_filepath: str, logger: LoggerBase, client_id: str):
    whisper_model = AUDIO_QUALITY_MAP.get(global_state.audio_quality, "distil-whisper/distil-large-v3")
    torch_compute_type = COMPUTE_TYPE_MAP.get(global_state.compute_type)
    logger.debug(f"Transcribing file path: {local_mp3_filepath}")
    # Send the filename w/o extension to the client. This becomes the name of the obsidian note.
    await ProcessUpdateManager.add_event(client_id, {'filename': os.path.splitext(os.path.basename(local_mp3_filepath))[0]})
    # If there are no chapters, it means the audio either didn't originate from YouTube or the YouTube metadata did not break the video into chapters.
    if not global_state.chapters:
        global_state.update(chapters=[{'start_time': 0.0, 'end_time': 0.0, 'title': ''}])
    chapters = global_state.chapters

    # Let the user know that the transcription will be transcribing by chapters.
    await ProcessUpdateManager.add_event(client_id, {'status': f'Transcribing {len(chapters)} chapter(s).'})
    await ProcessUpdateManager.add_event(client_id, {'num_chapters': len(chapters)})
    logger.debug(f"Number of chapters: {len(chapters)}")

    start_time = time.time()
    # Transcribed chapters are sent to Obsidian as they become available.
    async for chapter in transcribe_chapters(chapters, logger, local_mp3_filepath, whisper_model, torch_compute_type):
        await ProcessUpdateManager.add_event(client_id, chapter)
    end_time = time.time()
    transcription_time = round(end_time - start_time, 1)
    await ProcessUpdateManager.add_event(client_id, {'done': transcription_time})

# For use with more than one chapter, define a function to slice audio
def slice_audio(local_mp3_filepath: str, start_ms: int, end_ms: int) -> str:
    audio = AudioSegment.from_file(local_mp3_filepath)
    audio_segment = audio[start_ms:end_ms]
    temp_audio_path = "temp.wav"
    audio_segment.export(temp_audio_path, format="wav")
    return temp_audio_path



def transcribe_chapter(mp3_file: str, hf_model_name: str = "distil-whisper/distil-large-v3", compute_type_pytorch: torch.dtype = torch.float16) -> str:
    # Load model
    transcriber = pipeline("automatic-speech-recognition",
                           model=hf_model_name,
                           device=0 if torch.cuda.is_available() else -1,
                           torch_dtype=compute_type_pytorch)

    # Transcribe
    result = transcriber(mp3_file, chunk_length_s=30, batch_size=8)

    return result['text']

async def transcribe_chapters(chapters: list, logger: LoggerBase, local_mp3_filepath: str, hf_model_name: str = "distil-whisper/distil-large-v3", compute_type_pytorch: torch.dtype = torch.float16, client_id: str = None) :
    for chapter in chapters:
        logger.debug(f'transcribe_code.transcribe_chapters: processing chapter {chapter}')
        start_ms = int(chapter['start_time'] * 1000)
        end_ms = int(chapter['end_time'] * 1000) if chapter['end_time'] > 0.0 else None # None happens when input not from YouTube.
        title = chapter['title'] if len(chapter['title']) > 0 else None
        # Slice the audio if end_ms is provided, otherwise use the entire file
        mp3_path = slice_audio(local_mp3_filepath, start_ms, end_ms) if end_ms else local_mp3_filepath
        # Transcribe the audio segment
        transcription = transcribe_chapter(mp3_path, hf_model_name=hf_model_name, compute_type_pytorch=compute_type_pytorch)
        transcription_chapter = ''
        # Write to Markdown file
        if title:
            transcription_chapter += f"\n## {title}\n"
        if end_ms:
            # There are more than one chapter so add start and end times of where the text is with respect to the transcript.
            start_time_str = time.strftime('%H:%M:%S', time.gmtime(chapter['start_time']))
            end_time_str = time.strftime('%H:%M:%S', time.gmtime(chapter['end_time']))
            transcription_chapter += f"{start_time_str} - {end_time_str}\n"
        transcription_chapter += f"\n{transcription}"

        # Yield progress event for each chapter
        yield {'chapter': transcription_chapter}
