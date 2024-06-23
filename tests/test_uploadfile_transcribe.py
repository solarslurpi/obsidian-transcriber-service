
from dotenv import load_dotenv
load_dotenv()
import os
import torch

from fastapi import FastAPI, File, UploadFile, Form


from metadata_extractor_code import ChapterMetadata
from transcription_code import TranscribeAudio

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
app = FastAPI()

@app.post("/test_upload_file")
async def test_upload_file(file: UploadFile = File(...)):
    # Save the uploaded file to a directory
    c = ChapterMetadata(start=0, end=0)
    t = TranscribeAudio()
    mp3_file = save_local_mp3(file)
    chapter_text = await t.transcribe_chapter(mp3_file,"openai/whisper-tiny.en", torch.float16, c)

    # Save chapter_text to a file within the local directory.
    chapter_file = os.path.join(LOCAL_DIRECTORY, "chapter.txt")
    with open(chapter_file, "w") as file:
        file.write(chapter_text)


    return {"file properties": "hello"}

def save_local_mp3(upload_file: UploadFile):
    # Ensure the local directory exists
    if not os.path.exists(LOCAL_DIRECTORY):
        os.makedirs(LOCAL_DIRECTORY)

    file_location = os.path.join(LOCAL_DIRECTORY, upload_file.filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(upload_file.file.read())
        file_object.close()
    return file_location

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test:app", host="127.0.0.1", port=8001, reload=True)
