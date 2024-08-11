# Glossary
## Chapters
The transcript is broken into chapters. Two types of chapters:
1. YouTube chapters: If the YouTube video has Chapters metadata, the transcript is broken into those chapters. The YouTube chapters metadata contains a list of timestamps and corresponding chapter titles that divide a video into distinct, labeled sections, allowing viewers to easily navigate to specific parts of the video. These chapter titles typically represent the topic or subject matter of each section, providing contextual information.

2. Time-based chapters: If the YouTube video does not have Chapters metadata, the transcript is broken into time-based chapters. The transcript is divided into sections based on the time elapsed since the beginning of the video. The time-based chapters are created at regular intervals based on client input.  The default is 10 minutes per chapter.

## Metadata
If the metadata is from a YouTube video, the metadata can be quite extensive.  The fields included are defined within the [Metadata pydantic class](https://github.com/solarslurpi/obsidian-transcriber-service/blob/030fc45cb8fee3eef4fea68f1f9395ed150ea895/src/metadata_shared_code.py#L30).  The `TinyTag` library is used to extract the metadata from an audio file.  It is far less extensive than the YouTube metadata. See [_extract_audio_attributes](https://github.com/solarslurpi/obsidian-transcriber-service/blob/030fc45cb8fee3eef4fea68f1f9395ed150ea895/src/audio_handler_code.py#L52).
