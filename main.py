import argparse
import sys
import time
import threading
from pynput import keyboard
from recorder import Recorder
from transcriber import Transcriber
from typer import Typer
from feedback import Feedback

class VoiceTranscriptionCLI:
    def __init__(self, model_size="base", hotkey=keyboard.Key.f8):
        self.recorder = Recorder()
        self.transcriber = Transcriber(model_size=model_size)
        self.typer = Typer()
        self.feedback = Feedback()
        self.hotkey = hotkey
        self.is_recording = False
        self.processing_lock = threading.Lock()

    def on_press(self, key):
        if key == self.hotkey and not self.is_recording:
            with self.processing_lock:
                self.is_recording = True
                print("\nRecording... (release key to stop)")
                self.feedback.notify("🎙️ Recording...")
                self.recorder.start()

    def on_release(self, key):
        if key == self.hotkey and self.is_recording:
            with self.processing_lock:
                self.is_recording = False
                audio_data = self.recorder.stop()
                print("Processing transcription...")
                
                # Run transcription in a separate thread to not block the listener
                threading.Thread(target=self._process_and_type, args=(audio_data,), daemon=True).start()

    def _process_and_type(self, audio_data):
        text = self.transcriber.transcribe(audio_data)
        if text:
            print(f"Transcribed: {text}")
            self.typer.type_text(text)
            self.feedback.notify(f"✅ Transcribed: {text[:30]}...")
            self.feedback.play_beep()
        else:
            print("No speech detected.")
            self.feedback.notify("🔇 No speech detected.")

    def run(self):
        print(f"Voice Transcription CLI started.")
        print(f"Hotkey: {self.hotkey}")
        print("Press Ctrl+C to exit.")
        
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Voice Transcription CLI with PTT")
    parser.add_argument("--model", type=str, default="tiny", help="Whisper model size (tiny, base, small, medium, large-v3)")
    parser.add_argument("--key", type=str, default="f8", help="Hotkey for PTT (e.g. f8, ctrl_r)")
    
    args = parser.parse_args()

    # Map string key names to pynput Key attributes
    hotkey = getattr(keyboard.Key, args.key, None)
    if not hotkey:
        if len(args.key) == 1:
            hotkey = keyboard.KeyCode.from_char(args.key)
        else:
            print(f"Error: Unknown key '{args.key}'")
            sys.exit(1)

    app = VoiceTranscriptionCLI(model_size=args.model, hotkey=hotkey)
    app.run()

if __name__ == "__main__":
    main()
