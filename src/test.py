from typing import Optional
from fastapi import FastAPI, Form, File, UploadFile, Depends
from pydantic import BaseModel, Field

app = FastAPI()

class AudioProcessRequest(BaseModel):
    youtube_url: Optional[str] = None
    file: Optional[UploadFile] = None
    audio_quality: str = Field(default="default", description="Audio quality setting for processing.")
    source_type: str = Field(default="unknown", description="Indicates whether the source is a YouTube URL or a file.")

    @classmethod
    def as_form(
        cls,
        youtube_url: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        audio_quality: str = Form(default="default")
    ) -> "AudioProcessRequest":
        return cls(youtube_url=youtube_url, file=file, audio_quality=audio_quality)

@app.post("/api/v1/process_audio")
async def process_audio(
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    audio_quality: str = Form(default="default")
):
    request = AudioProcessRequest.as_form(youtube_url=youtube_url, file=file, audio_quality=audio_quality)
    return request

# # To test this, you can use the FastAPI interactive docs or send a POST request with form data to /process_audio
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("test:app", host="127.0.0.1", port=8000)