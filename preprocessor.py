import numpy as np
from scipy import signal


class AudioPreprocessor:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

        # Band-pass filter parameters
        # Speech fundamentals are 85Hz-255Hz, harmonics go up to 8kHz
        # We filter out rumble (<80Hz) and high frequency hiss (>8000Hz)
        self.low_cutoff = 80.0
        # Nyquist is 8000Hz for 16kHz. Cutoff must be < 1.0 * Nyquist.
        # We set it to 7500Hz to be safe and avoid edge artifacts.
        self.high_cutoff = 7500.0
        self.filter_order = 5

        # Pre-calculate filter coefficients (Butterworth filter)
        nyquist = 0.5 * self.sample_rate
        low = self.low_cutoff / nyquist
        high = self.high_cutoff / nyquist
        self.b, self.a = signal.butter(self.filter_order, [low, high], btype="band")

    def process(self, audio_data):
        """
        Apply band-pass filtering and normalization to audio data.

        Args:
            audio_data (np.array): Raw float32 audio data from recorder

        Returns:
            np.array: Processed audio data
        """
        if audio_data is None or len(audio_data) == 0:
            return audio_data

        # 1. Band-pass Filter
        # Removes AC hum, desk thumps, and high-pitch hiss
        filtered_audio = signal.filtfilt(self.b, self.a, audio_data)

        # 2. Normalization
        # Boosts quiet speech to a consistent level (-1.0 dB peak)
        # We use a safe maximum to avoid blowing out ears if there's a loud pop
        max_val = np.max(np.abs(filtered_audio))

        if max_val > 0:
            # Target peak amplitude: 0.9 (approx -1.0 dB)
            target_peak = 0.9

            # Don't amplify noise if the signal is silence
            # (If max peak is below 0.01, it's probably just background noise)
            if max_val > 0.01:
                normalization_factor = target_peak / max_val
                # Cap the boost to 10x (20dB) to prevent exploding background noise
                normalization_factor = min(normalization_factor, 10.0)

                filtered_audio = filtered_audio * normalization_factor

        return filtered_audio.astype(np.float32)
