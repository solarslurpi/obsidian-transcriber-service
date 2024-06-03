from typing import List, Optional
from pydantic import BaseModel, Field

class Chapter(BaseModel):
    title: str = Field(..., description="Title of the chapter.")
    start: int = Field(..., description="Start time of the chapter in seconds.")
    end: int = Field(..., description="End time of the chapter in seconds.")
    transcription: Optional[str] = Field(None, description="Transcription for the chapter.")

def create_chapters(info_dict):
    chapters_info = info_dict.get('chapters', [{'start_time': 0.0, 'end_time': 0.0, 'title': '', 'transcription': None}])
    chapters = [Chapter(title=chap['title'], start=chap['start_time'], end=chap['end_time'], transcription=chap.get('transcription')) for chap in chapters_info]
    return chapters

# Test data
info_dict = {
    'chapters': [
        {'start_time': 0, 'end_time': 10, 'title': 'Chapter 1', 'transcription': 'This is chapter 1'},
        {'start_time': 10, 'end_time': 20, 'title': 'Chapter 2'}
    ]
}

chapters = create_chapters(info_dict)

for chapter in chapters:
    print(f"Title: {chapter.title}, Start: {chapter.start}, End: {chapter.end}, Transcription: {chapter.transcription}")