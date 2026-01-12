from faster_whisper import WhisperModel
import logging

# Suppress faster-whisper logs if needed
# logging.getLogger("faster_whisper").setLevel(logging.WARNING)

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        print(f"Loading Whisper model '{model_size}' on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_data):
        if audio_data is None or len(audio_data) == 0:
            return ""
        
        segments, info = self.model.transcribe(audio_data, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()
