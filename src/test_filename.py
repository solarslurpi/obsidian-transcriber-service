
import yt_dlp
import logging
import os
# Setup logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('yt-dlp')

def download_video(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'restrict-filenames': True,
        'writeinfojson': True,
        'replace-in-metadata': {
            'title': {'：': '_', ':': '_'},  # Replace full-width and standard colons
        },
        'outtmpl': 'local/%(title)s.%(ext)s',
        'logger': logger,
        'verbose': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '12',
        }],
    }
    # When downloading, tghe info_dict['requested_downloads'] will contain a list of details about each file downloaded.  The code supports downloading one file, so [0] is used to get the first item that we want - this is the filepath field.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
    return info_dict

# Test the function
info_dict = download_video('https://www.youtube.com/watch?v=E4eILFEy8gw')

mp3_filepath = info_dict['requested_downloads'][0]['filepath']
print(f"MP3 filepath: {mp3_filepath}")
print(f"The file: {info_dict['requested_downloads'][0]['filename']} exists: {os.path.exists(mp3_filepath)}")
# Build the filepath based on the expected filename given ydl_opts
# mp3filepath = 'local'

# # used for testing.  file = r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\local\Focus on： Substrate Components Impact on Substrate pH.mp3"
#