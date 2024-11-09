from faster_whisper import WhisperModel

# Create model
model = WhisperModel("tiny", device="cuda", compute_type="int8")
print("Model loaded successfully!")

# Try a simple transcription
segments, info = model.transcribe("test.mp3")
print("Transcription successful!")