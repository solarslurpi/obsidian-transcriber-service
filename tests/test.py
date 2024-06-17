import torch

from metadata_code import ChapterMetadata


from transcription_state_code import ChapterTranscript, TranscriptionState

chapters = [
    ChapterTranscript(ChapterMetadata=ChapterMetadata(title="Introduction", start=0, end=300), transcript="Transcript for chapter 1"),
    ChapterTranscript(ChapterMetadata=ChapterMetadata(title="Chapter 1: Getting Started", start=301, end=900), transcript="Transcript for chapter 2"),
    ChapterTranscript(ChapterMetadata=ChapterMetadata(title="Chapter 2: Advanced Topics", start=901, end=1800), transcript="Transcript for chapter 3")
]

chapters = [
    ChapterTranscript(ChapterMetadata=ChapterMetadata(title="Introduction", start=0, end=300)),
    ChapterTranscript(ChapterMetadata=ChapterMetadata(title="Chapter 1: Getting Started", start=301, end=900)),
    ChapterTranscript(ChapterMetadata=ChapterMetadata(title="Chapter 2: Advanced Topics", start=901, end=1800))
]
state = TranscriptionState(hf_compute_type=torch.float32, hf_model='facebook/wav2vec2-base-960h',chapters=chapters)
print(state)