import argparse
import fcntl
import os
import sys
import threading

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
        print(
            "\n[!] Error: Another instance of Voice Transcription CLI is already running."
        )
        print(
            f"[!] Check for background processes or remove {LOCK_FILE} if no process exists."
        )
        sys.exit(1)


def bootstrap():
    """Ensure CUDA libraries are in the LD_LIBRARY_PATH and restart if necessary."""
    import site

    packages = site.getsitepackages()
    if hasattr(site, "getusersitepackages"):
        packages.append(site.getusersitepackages())

    cuda_paths = []
    for p in packages:
        cublas_path = os.path.join(p, "nvidia", "cublas", "lib")
        cudnn_path = os.path.join(p, "nvidia", "cudnn", "lib")
        if os.path.exists(cublas_path):
            cuda_paths.append(cublas_path)
        if os.path.exists(cudnn_path):
            cuda_paths.append(cudnn_path)

    if not cuda_paths:
        return  # No libraries to add

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

    from corrector import Corrector
    from feedback import Feedback
    from preprocessor import AudioPreprocessor
    from recorder import Recorder
    from transcriber import Transcriber
    from typer import Typer

    class VoiceTranscriptionCLI:
        def __init__(
            self, model_size="large-v3-turbo", hotkey=keyboard.Key.f8, enable_ui=True
        ):
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
                    print(
                        f"Warning: Could not load UI ({e}). Running without floating window."
                    )
                    self.floating_ui = None
                except Exception as e:
                    print(
                        f"Warning: UI initialization failed ({e}). Running without floating window."
                    )
                    self.floating_ui = None

            # Create amplitude callback for UI updates
            def on_amplitude(amp):
                if self.floating_ui:
                    self.floating_ui.update_amplitude(amp)

            self.recorder = Recorder(
                on_amplitude=on_amplitude if self.floating_ui else None
            )
            self.transcriber = Transcriber(model_size=model_size)
            self.corrector = Corrector()
            self.typer = Typer()
            self.feedback = Feedback()
            self.preprocessor = AudioPreprocessor()

            self.hotkey = hotkey
            self.is_recording = False
            self.shift_pressed = False
            self.processing_lock = threading.Lock()

        def on_press(self, key):
            # Track shift state
            if key == keyboard.Key.shift or key == keyboard.Key.shift_r:
                self.shift_pressed = True

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
            # Track shift state
            if key == keyboard.Key.shift or key == keyboard.Key.shift_r:
                self.shift_pressed = False

            if key == self.hotkey and self.is_recording:
                with self.processing_lock:
                    self.is_recording = False
                    audio_data = self.recorder.stop()

                    # Capture shift state at moment of release for override
                    force_terminal = self.shift_pressed

                    # Hide floating UI
                    if self.floating_ui:
                        self.floating_ui.hide()

                    print("Processing transcription...")
                    threading.Thread(
                        target=self._process_and_type,
                        args=(audio_data, force_terminal),
                        daemon=True,
                    ).start()

        def _process_and_type(self, audio_data, force_terminal=False):
            # 1. Pre-process audio (Normalize + Bandpass)
            processed_audio = self.preprocessor.process(audio_data)

            # 2. Transcribe
            text = self.transcriber.transcribe(processed_audio)

            if text:
                # 3. Post-process text
                corrected_text = self.corrector.correct(text)
                print(f"Transcribed: {corrected_text}")

                # 4. Type text with context awareness
                # force_terminal comes from Shift key state on release
                self.typer.type_text(corrected_text, force_terminal=force_terminal)

                self.feedback.notify(f"✅ Transcribed: {corrected_text[:30]}...")
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
            with keyboard.Listener(
                on_press=self.on_press, on_release=self.on_release
            ) as listener:
                try:
                    listener.join()
                except KeyboardInterrupt:
                    print("\nExiting...")
                    if self.floating_ui:
                        self.floating_ui.stop()
                    sys.exit(0)

    def main():
        parser = argparse.ArgumentParser(description="Voice Transcription CLI with PTT")
        parser.add_argument(
            "--model", type=str, default="large-v3-turbo", help="Whisper model size"
        )
        parser.add_argument("--key", type=str, default="f8", help="Hotkey for PTT")
        parser.add_argument(
            "--no-ui", action="store_true", help="Disable floating UI window"
        )
        args = parser.parse_args()

        hotkey = getattr(keyboard.Key, args.key, None)
        if not hotkey:
            if len(args.key) == 1:
                hotkey = keyboard.KeyCode.from_char(args.key)
            else:
                print(f"Error: Unknown key '{args.key}'")
                sys.exit(1)

        app = VoiceTranscriptionCLI(
            model_size=args.model, hotkey=hotkey, enable_ui=not args.no_ui
        )
        app.run()

    main()
