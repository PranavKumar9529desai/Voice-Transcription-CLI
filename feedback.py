import subprocess
import os
import wave
import struct
import math

class Feedback:
    def __init__(self):
        self.beep_path = "/tmp/transcription_beep.wav"
        self._ensure_beep_exists()

    def _ensure_beep_exists(self):
        """Generate a simple sine wave beep if it doesn't exist."""
        if os.path.exists(self.beep_path):
            return
            
        sample_rate = 44100
        duration = 0.1  # seconds
        frequency = 880  # Hz (A5)
        
        with wave.open(self.beep_path, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            for i in range(int(duration * sample_rate)):
                value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                f.writeframesraw(struct.pack('<h', value))

    def notify(self, message, timeout=2000):
        """Show a desktop notification."""
        try:
            subprocess.run(["notify-send", "-t", str(timeout), "Voice Transcriber", message], check=False)
        except Exception:
            pass

    def play_beep(self):
        """Play a subtle blip sound."""
        try:
            # aplay is standard on Ubuntu
            subprocess.Popen(["aplay", "-q", self.beep_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
