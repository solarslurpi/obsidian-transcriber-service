
import json
import os

from typing import Dict

import yt_dlp

# The actual name of the directory/folder holding file writes
LOCAL = os.getenv("LOCAL_DIRECTORY")
# The location will be below the parent of the current directory.
current_directory = os.getcwd()
parent_directory = os.path.dirname(current_directory)
LOCAL_DIRECTORY = f"{parent_directory}/{LOCAL}"

# Ensure the local directory exists
if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

def get_info_dict(youtube_url):
    ydl_opts = {
        'outtmpl': '%(title)s',
        'quiet': True,
        'simulate': True,
        'getfilename': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
    return info_dict

def add_info_dict_to_file(info_dict: Dict):
    data = []
    filepath = f"{LOCAL_DIRECTORY}/test_metadata.json"
    if os.path.exists(filepath):
        # If file exists, load the existing data
        with open(filepath, 'r') as f:
            data = json.load(f)
    # remove the keys we are not interested in and contain alot of charcters.
    keys_to_remove = ['formats', 'thumbnails', '_format_sort_fields','requested_formats','automatic_captions']
    for key in keys_to_remove:
        info_dict.pop(key, None)  # Use None as default to avoid KeyError if the key doesn't exist

    # append the new dictionary
    data.append(info_dict)
    # write the entire list back to the file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)



def main():
    youtube_urls = [
        "https://www.youtube.com/watch?v=KbZDsrs5roI",
        "https://www.youtube.com/watch?v=xJ6X7LiG3No&list=PLfr8_WtlUhJmPZRiAdzIjAAk5xQhuZKG3",
        "https://www.youtube.com/watch?v=YoiGS1Rlqlo",
        "https://www.youtube.com/watch?v=LtJDVSFpi-w"
    ]

    for index, url in enumerate(youtube_urls):
        print("\n------------------------\n")
        print(f"{index} Processing {url}")
        info_dict = get_info_dict(url)

        print(f"Adding info dict , title: {info_dict['title']} to file.")
        add_info_dict_to_file(info_dict)

if __name__ == "__main__":
    main()