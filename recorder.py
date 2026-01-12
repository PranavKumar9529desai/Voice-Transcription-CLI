import sounddevice as sd
import numpy as np
import threading
import queue

class Recorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.stream = None
        self.audio_data = []

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Recording status: {status}")
        if self.recording:
            self.audio_data.append(indata.copy())

    def start(self):
        print("Recorder started")
        self.audio_data = []
        self.recording = True
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, callback=self._callback)
        self.stream.start()

    def stop(self):
        print("Recorder stopped")
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if not self.audio_data:
            return np.array([], dtype='float32')
            
        return np.concatenate(self.audio_data, axis=0).flatten()
