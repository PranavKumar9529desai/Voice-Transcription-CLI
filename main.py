import os
import sys
import argparse
import fcntl
from pynput import keyboard

LOCK_FILE = "/tmp/voice-transcription.lock"

def ensure_single_instance():
    """Prevent multiple instances from running simultaneously."""
    global lock_file_handle
    lock_file_handle = open(LOCK_FILE, "wb")
    try:
        # Try to acquire an exclusive lock without blocking
        fcntl.flock(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("\n[!] Error: Another instance of Voice Transcription CLI is already running.")
        print(f"[!] Check for background processes or remove {LOCK_FILE} if no process exists.")
        sys.exit(1)

def bootstrap():
    """Ensure CUDA libraries are in the LD_LIBRARY_PATH and restart if necessary."""
    import site
    packages = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        packages.append(site.getusersitepackages())
    
    cuda_paths = []
    for p in packages:
        cublas_path = os.path.join(p, "nvidia", "cublas", "lib")
        cudnn_path = os.path.join(p, "nvidia", "cudnn", "lib")
        if os.path.exists(cublas_path): cuda_paths.append(cublas_path)
        if os.path.exists(cudnn_path): cuda_paths.append(cudnn_path)
            
    if not cuda_paths:
        return # No libraries to add

    current_ld = os.environ.get("LD_LIBRARY_PATH", "")
    # Check if we already have the paths in LD_LIBRARY_PATH
    needs_restart = False
    for path in cuda_paths:
        if path not in current_ld:
            needs_restart = True
            break
            
    if needs_restart:
        print("Optimizing environment for GPU access...")
        new_ld = ":".join(cuda_paths + ([current_ld] if current_ld else []))
        os.environ["LD_LIBRARY_PATH"] = new_ld
        # Restart the process with the new environment
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    # Must be first
    ensure_single_instance()
    bootstrap()
    
    from recorder import Recorder
    from transcriber import Transcriber
    from typer import Typer
    from feedback import Feedback
    import threading

    class VoiceTranscriptionCLI:
        def __init__(self, model_size="distil-large-v3", hotkey=keyboard.Key.f8):
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
        parser.add_argument("--model", type=str, default="distil-large-v3", help="Whisper model size")
        parser.add_argument("--key", type=str, default="f8", help="Hotkey for PTT")
        args = parser.parse_args()

        hotkey = getattr(keyboard.Key, args.key, None)
        if not hotkey:
            if len(args.key) == 1:
                hotkey = keyboard.KeyCode.from_char(args.key)
            else:
                print(f"Error: Unknown key '{args.key}'")
                sys.exit(1)

        app = VoiceTranscriptionCLI(model_size=args.model, hotkey=hotkey)
        app.run()

    main()
