import time
from faster_whisper import WhisperModel

start_time = time.time()
# Run on GPU with FP16
model = WhisperModel("small", device="cuda", compute_type="int8")
end_time = time.time()
print(f"Time taken to load model: {end_time - start_time}")
# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")
start_time = time.time()


segments, info = model.transcribe(r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\tests\audio_files\test.mp3", beam_size=5, temperature=0.0)



with open("transcription_segments.txt", "w") as f:
    for segment in segments:
        segment_text = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        print(segment_text)
        f.write(segment_text + "\n")

end_time = time.time()

print("Transcription took %.2f seconds" % (end_time - start_time))
print("Detected language '%s' with probability %f" % (info.language, info.language_probability))