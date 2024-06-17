import torch
from transcription_state_code import TranscriptionState, ChapterTranscript

local_mp3 = "test/local.mp3"
description = "This is a test transcription"
hf_model = "hf_model"
hf_compute_type = torch.float16
chapters = []
chapter_1 = ChapterTranscript(title="Chapter 1", start=0, end=10, transcription="This is chapter 1")
chapters.append(chapter_1)

state = TranscriptionState(local_mp3=local_mp3, description=description, hf_model=hf_model, hf_compute_type=hf_compute_type, chapters=chapters)
print(state)