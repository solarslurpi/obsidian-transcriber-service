
from audio_handler_code import AudioHandler
from audio_processing_model import AudioProcessRequest


async def process_audio():
    audio_input = AudioProcessRequest(audio_file=r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\audio_files\test.mp3")
    audio_handler = AudioHandler(audio_input=audio_input)
    metadata, chapters, audio_filepath = await audio_handler.extract()
    return metadata, chapters, audio_filepath


# Write async main function to run the process_audio function
# and save the metadata to a file
async def main():
    print("hello")
    metadata, chapters, audio_filepath = await process_audio()
    # save metadata to tests/metadata_mp3.json
    with open(r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\metadata_mp3.json", "w") as file:
        file.write(metadata.model_dump_json())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())