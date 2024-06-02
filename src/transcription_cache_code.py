

from pydantic_models import global_state

class TranscriptionCache:
    '''Manage the state of the transcription content with the intent of providing a way to update the client with cached results if the audio has already been transcribed or is in process.'''
    caches = []
    def __init__(self, cache_key:str):
        # chapter_metadata is a dictionary with keys 'start_time', 'end_time', and 'transcription'.  On init, the chapters should include the start and stop times of the audio.  The transcription is empty at this point, unless the cache for this cache_key already exists.
        self.cache_key = cache_key
        # Note: Interesting AFTER we have the audio - i.e.: after YT download if that is part of the process.
        # We initialize after we get chapter info from the audio part.
        # Chapters is a list of dictionaries with keys 'start_time', 'end_time', and 'transcription'.  On init, the chapters should include the start and stop times of the audio and the transcription of the audio.
        # The cache_key contains the base mp3 filename and the audio quality of the transcript. This uniquely identifies the audio file. transcripton_cache_key = (audio_input.youtube_url or audio_input.file, audio_input.audio_quality).

        # Get Chapter info from the global_state.  Since audio processing happens before transcription, we should have chapter info available.
        if not global_state.chapters:
            raise ValueError('No chapters available in global_state.  Please restart the transcription.')
        # Check if the cache already exists.
        if not any(cache['key'] == cache_key for cache in TranscriptionCache.caches):
            TranscriptionCache.caches.append({'key': cache_key,
                                              'basefilename': global_state.basefilename,
                                              'chapters': global_state.chapters})  # Use class variable here


    def add_chapter(self, start_time,  transcription=None):
        # Find the correct cache
        cache = self._find_cache()
        # Find the chapter with the matching start and end times
        for chapter in cache['chapters']:
            # The start and end time were given to us by the metadata.
            if chapter['start_time'] == start_time :
                # Update the transcription of the found chapter
                chapter['transcription'] = transcription
                break
        else:
            # If no matching chapter is found, raise an error
            raise ValueError(f"No chapter found with start time {start_time}")
    @property
    def num_chapters_with_transcripts(self):
        cache = self._find_cache()
        if cache:
            return sum(1 for chapter in cache['chapters'] if chapter.get('transcription'))
        else:
            return 0
    @property
    def num_chapters_total(self):
        cache = self._find_cache()
        if cache:
            return len(cache['chapters'])
        else:
            return 0

    def get_chapters(self):
        # Go through each transcription cache to see if there is a match
        cache = self._find_cache()
        return cache['chapters'] if cache else None

    def clear_cache(self):
        # Go through each transcription cache to see if there is a match
        cache = self._find_cache()
        if cache:
            cache['chapters'] = []
            return True
        return False

    def _find_cache(self):
        for cache in TranscriptionCache.caches:
            if cache['key'] == self.cache_key:
                return cache
        return None