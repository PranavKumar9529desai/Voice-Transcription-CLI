import os
import subprocess
import time
from pynput import keyboard

class Typer:
    def __init__(self):
        self.controller = keyboard.Controller()
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
        print(f"Typer initialized for session: {self.session_type}")

    def type_text(self, text):
        if not text:
            return

        if self.session_type == "wayland":
            self._type_wayland(text)
        else:
            self._type_x11(text)

    def _type_x11(self, text):
        """X11 implementation using xclip and xdotool."""
        try:
            # 1. Copy to selection (primary) and clipboard
            subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
            
            # 2. Small delay
            time.sleep(0.05)

            # 3. Paste using xdotool (Ctrl+v)
            # We use xdotool because it's often more reliable than pynput in X11 for global injection
            subprocess.run(["xdotool", "key", "ctrl+v"], check=True)
            print("Pasted via xdotool.")
        except FileNotFoundError:
            print("Error: 'xclip' or 'xdotool' not found. Please install them: sudo apt install xclip xdotool")
            # Fallback to pynput
            self._fallback_pynput_paste()
        except Exception as e:
            print(f"X11 Injection failed: {e}")
            self._fallback_pynput_paste()

    def _type_wayland(self, text):
        """Wayland implementation using wl-copy and ydotool."""
        try:
            subprocess.run(["wl-copy", text], check=True)
            time.sleep(0.05)
            
            # Strategy: Try ydotool first as it's wayland-native hardware emulation
            try:
                # Keycodes: Ctrl (29), V (47)
                subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=True, capture_output=True)
                print("Pasted via ydotool.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to pynput if ydotool/ydotoold is not available
                self._fallback_pynput_paste()
        except FileNotFoundError:
            print("Error: 'wl-clipboard' not found. Please install it.")
        except Exception as e:
            print(f"Wayland Injection failed: {e}")

    def _fallback_pynput_paste(self):
        """Standard pynput Ctrl+V fallback."""
        try:
            with self.controller.pressed(keyboard.Key.ctrl):
                self.controller.press('v')
                self.controller.release('v')
            print("Pasted via pynput fallback.")
        except Exception as e:
            print(f"Fallback paste failed: {e}")
