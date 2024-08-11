

The Whisper model is used to transcribe the text.  I tried the Hugging Face pipeline, moved to the OpenAI package, then settled on faster-whisper because it had the fastest transcription time.

## Segments
Transcriptions are returned from faster-whisper in (30 second) segments. The following keys are available (see [faster-whisper/transcribe.py](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py)):

```
class Segment(NamedTuple):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: Optional[List[Word]]
    temperature: Optional[float] = 1.0
```

## Chapters
The transcript is broken into either chunks of time or topic if the video has been split into chapters.


- if the transcript is less than the max chapter time, the transcript is returned as a single chapter.
