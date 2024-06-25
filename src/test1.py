import os
import re
from dotenv import load_dotenv
load_dotenv()

LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
def _sanitize_filename(current_mp3_filepath: str) -> str:
    def cleaned_name(uncleaned_name:str) -> str:
        # Remove non-alphanumeric characters except for spaces, periods, and hyphens.
        cleaned_name = re.sub(r"[^a-zA-Z0-9 \.-]", "", uncleaned_name)
        # Replace spaces with underscores.
        cleaned_name = cleaned_name.replace(" ", "_")
        # Replace full-width colons and standard colons with a hyphen or other safe character
        cleaned_name = cleaned_name.replace('：', '_').replace(':', '_')
        return cleaned_name

    current_mp3_basename = os.path.splitext(os.path.basename(current_mp3_filepath))[0]
    cleaned_mp3_filename = cleaned_name(current_mp3_basename) + ".mp3"
    cleaned_mp3_filepath = os.path.join(LOCAL_DIRECTORY, cleaned_mp3_filename)
    os.rename(current_mp3_filepath, cleaned_mp3_filepath)
    return cleaned_mp3_filepath

current_mp3_filepath = r'C:\Users\happy\Documents\Projects\obsidian-transcriber-service\local\Focus on： Substrate Components Impact on Substrate pH.mp3'

mp3_filepath = _sanitize_filename(current_mp3_filepath)
print(f"Current mp3 filepath: {current_mp3_filepath}")
print(f"Sanitized mp3 filepath: {mp3_filepath}")
