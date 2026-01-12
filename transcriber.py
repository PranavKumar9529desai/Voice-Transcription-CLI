from faster_whisper import WhisperModel
import ctranslate2
import logging

class Transcriber:
    def __init__(self, model_size="distil-large-v3", device=None, compute_type="float16"):
        if device is None:
            # Auto-detect CUDA
            if ctranslate2.get_cuda_device_count() > 0:
                device = "cuda"
            else:
                device = "cpu"
                compute_type = "int8"
                print("GPU not detected, falling back to CPU.")
        
        print(f"Loading Whisper model '{model_size}' on {device} ({compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_data):
        if audio_data is None or len(audio_data) == 0:
            return ""
        
        segments, info = self.model.transcribe(
            audio_data, 
            beam_size=5, 
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        text = "".join([segment.text for segment in segments])
        return text.strip()
