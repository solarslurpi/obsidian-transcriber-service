import time
from faster_whisper import WhisperModel, BatchedInferencePipeline


start_time = time.time()
model = WhisperModel("tiny.en", device="cuda", compute_type="int8")
end_time = time.time()
print(f"Time taken to load model: {end_time - start_time}")

start_time = time.time()
batched_model = BatchedInferencePipeline(model=model)
segments, info = batched_model.transcribe(r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\audio_files\test.mp3", batch_size=16)

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

with open("transcription_segments.txt", "w") as f:
    for segment in segments:
        segment_text = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        print(segment_text)
        f.write(segment_text + "\n")

end_time = time.time()

print("Transcription took %.2f seconds" % (end_time - start_time))
print("Detected language '%s' with probability %f" % (info.language, info.language_probability))