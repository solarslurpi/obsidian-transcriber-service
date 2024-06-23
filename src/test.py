import asyncio
import re
import yt_dlp
from functools import partial

# Define an asyncio Queue
status_queue = asyncio.Queue()

class ProgressHookException(Exception):
    def __init__(self, message="A custom error occurred"):
        self.message = message
        super().__init__(self.message)

# Define the yt_dlp hook function with queue and loop
def progress_hook(info_dict, queue, loop):
    if info_dict['status'] == 'finished' or info_dict['status'] == 'downloading':
        try:
            # Regular expression to remove non-printable characters and color codes
            default_message = info_dict['_default_template']
            message = re.sub(r'\x1b\[.*?m', '', default_message)  # Remove ANSI escape sequences
            message = re.sub(r'\s+', ' ', message).strip()  # Replace multiple spaces with a single space
            print(message)
            asyncio.run_coroutine_threadsafe(queue.put(message), loop)
            if info_dict['status'] == 'finished':
                asyncio.run_coroutine_threadsafe(queue.put("done"), loop)
        except ProgressHookException as e:
            print(f'Error: {e}')
            raise e

# Set up yt_dlp options with the progress hook
def get_ydl_opts(queue, loop):
    return {
        'progress_hooks': [partial(progress_hook, queue=queue, loop=loop)],
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96', # 96 kbps was chosen as a good balance between quality and file size for the audio text.
        }],
        # The post processor args are settings best for (whisper) transcription.
        'postprocessor_args': [ # Settings best for transcription
            '-ac', '1', # Convert to mono
            '-ar', '44100' # Set sampling rate to 44.1 kHz
        ],
    }

# Function to run yt_dlp synchronously
def download_video(url, queue, loop):
    print("--- Starting download ---")
    ydl_opts = get_ydl_opts(queue, loop)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Async function to process status updates
async def process_status_updates(queue):
    while True:
        status = await queue.get()
        # Process the status update
        print(f"Processing queue: {status}")
        if status == 'done':
            break

# Main function to run the download in an asyncio task and process updates asynchronously
async def main(url):
    loop = asyncio.get_event_loop()

    # Run the download in a separate thread using asyncio.to_thread. yt_dlp is synchronous.
    # If the download is run on the main thread, it will block the event loop which the rest of the
    # code - like processing status updates - relies on.
    download_task = asyncio.create_task(asyncio.to_thread(download_video, url, status_queue, loop))

    # run both coroutines concurrently
    await asyncio.gather(
        process_status_updates(status_queue),
        download_task
    )
    print('--- Download complete ---')
# Run the main function
url = 'https://www.youtube.com/watch?v=KbZDsrs5roI'  # replace with your video URL
asyncio.run(main(url))
