import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
from faster_whisper import WhisperModel

def test_audio_and_whisper():
    fs = 16000  # Sample rate
    seconds = 3  # Duration of recording

    print(f"Recording for {seconds} seconds...")
    try:
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()  # Wait until recording is finished
        print("Recording finished.")
    except Exception as e:
        print(f"Error during recording: {e}")
        return

    # Flatten recording
    audio_data = myrecording.flatten()

    print("Loading Whisper model (tiny)...")
    model_size = "tiny"
    # Run on CPU with int8 quantization for speed in testing
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print("Transcribing...")
    segments, info = model.transcribe(audio_data, beam_size=5)

    print("Result:")
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

if __name__ == "__main__":
    test_audio_and_whisper()
