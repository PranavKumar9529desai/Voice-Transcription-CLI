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
        def __init__(self, model_size="distil-large-v3", hotkey=keyboard.Key.f8, enable_ui=True):
            self.enable_ui = enable_ui
            self.floating_ui = None
            
            # Initialize UI first if enabled
            if self.enable_ui:
                try:
                    from ui import FloatingWindow
                    self.floating_ui = FloatingWindow()
                    self.floating_ui.start()
                    print("Floating UI initialized")
                except ImportError as e:
                    print(f"Warning: Could not load UI ({e}). Running without floating window.")
                    self.floating_ui = None
                except Exception as e:
                    print(f"Warning: UI initialization failed ({e}). Running without floating window.")
                    self.floating_ui = None
            
            # Create amplitude callback for UI updates
            def on_amplitude(amp):
                if self.floating_ui:
                    self.floating_ui.update_amplitude(amp)
            
            self.recorder = Recorder(on_amplitude=on_amplitude if self.floating_ui else None)
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
                    
                    # Show floating UI
                    if self.floating_ui:
                        self.floating_ui.show()
                    
                    self.recorder.start()

        def on_release(self, key):
            if key == self.hotkey and self.is_recording:
                with self.processing_lock:
                    self.is_recording = False
                    audio_data = self.recorder.stop()
                    
                    # Hide floating UI
                    if self.floating_ui:
                        self.floating_ui.hide()
                    
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
            if self.floating_ui:
                print("Floating UI: Enabled")
            else:
                print("Floating UI: Disabled")
            print("Press Ctrl+C to exit.")
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                try:
                    listener.join()
                except KeyboardInterrupt:
                    print("\nExiting...")
                    if self.floating_ui:
                        self.floating_ui.stop()
                    sys.exit(0)

    def main():
        parser = argparse.ArgumentParser(description="Voice Transcription CLI with PTT")
        parser.add_argument("--model", type=str, default="distil-large-v3", help="Whisper model size")
        parser.add_argument("--key", type=str, default="f8", help="Hotkey for PTT")
        parser.add_argument("--no-ui", action="store_true", help="Disable floating UI window")
        args = parser.parse_args()

        hotkey = getattr(keyboard.Key, args.key, None)
        if not hotkey:
            if len(args.key) == 1:
                hotkey = keyboard.KeyCode.from_char(args.key)
            else:
                print(f"Error: Unknown key '{args.key}'")
                sys.exit(1)

        app = VoiceTranscriptionCLI(
            model_size=args.model, 
            hotkey=hotkey,
            enable_ui=not args.no_ui
        )
        app.run()

    main()

