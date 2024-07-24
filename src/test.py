import json
import os

from metadata_shared_code import Metadata

YOUTUBE_CACHE_FILEPATH = os.path.join(os.getenv("YOUTUBE_CACHE_DIRECTORY", "youtube_cache"), "youtube_cache.json")
youtube_url = 'https://www.youtube.com/watch?v=KbZDsrs5roI'

def get_entry(youtube_url):
    with open(YOUTUBE_CACHE_FILEPATH, 'r') as f:
        cache_data = json.load(f)
        for entry in cache_data:
            if youtube_url in entry["metadata"]["youtube_url"]:
                return entry['metadata'], entry['chapter_dicts'], entry['mp3_filepath']
        return None


metadata_dict, chapter_dicts, audio_filepath = get_entry(youtube_url)
metadata = Metadata(**metadata_dict)
print(f"metadata: {metadata}")