import asyncio
import os

from youtube_handler_code import YouTubeHandler

'c:\\Users\\happy\\Documents\\Projects\\obsidian-transcriber-service\\local\\Focus on： Substrate Components Impact on Substrate pH.mp3'
# Assuming the YouTubeHandler class and all necessary imports and global variables (like LOCAL_DIRECTORY) are defined above.

class App:
    def __init__(self, youtube_url):
        self.youtube_url = youtube_url
        self.mp3_filepath = None

    async def download_video(self):
        youtube_handler = YouTubeHandler(audio_input=self)
        metadata, chapters, self.mp3_filepath = await youtube_handler.extract()
        print(f"Downloaded video metadata: {metadata}")
        print(f"Chapters: {chapters}")
        print(f"MP3 file saved to: {self.mp3_filepath}")


    def run(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.download_video())

    def check_file_exists(self, filepath):
        return os.path.exists(filepath)

# The file is automatically closed here, outside the with block

if __name__ == "__main__":
    # Example YouTube URL
    youtube_url = "https://www.youtube.com/watch?v=E4eILFEy8gw"
    app = App(youtube_url)
    app.run()
    print(f"File exists: {app.check_file_exists(app.mp3_filepath)}")