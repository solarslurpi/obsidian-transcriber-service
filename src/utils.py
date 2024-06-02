

from pydantic_models import AudioProcessRequest, TranscriptionCache
from youtube_download_code import YouTubeDownloader
def have_local_mp3_and_chapters(audio_input: AudioProcessRequest) -> bool:
    # audio_input has either a youtube url or a an mp3 file.  If it is a youtube url, the url
    # is in the metadata. If it is an mp3 file, the file name in the local storage is the local_mp3 in the
    # metadata.
    pass

def look_up_transcription_cache(audio_input: AudioProcessRequest) -> bool:

    if YouTubeDownloader.isYouTube_url(audio_input):
        for _, transcription_state in TranscriptionCache.cache.items():
            if transcription_state.youtube_url == audio_input.youtube_url:
                return transcription_state
        return None

    else:
        for _, transcription_state in TranscriptionCache.cache.items():
            if transcription_state.local_mp3 == audio_input.file.filename:
                return transcription_state
        return None
