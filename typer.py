import subprocess
import time
from pynput import keyboard

class Typer:
    def __init__(self):
        self.controller = keyboard.Controller()

    def _get_current_clipboard(self):
        """Save current clipboard content (optional, advanced)."""
        try:
            return subprocess.check_output(["wl-paste"], text=True)
        except Exception:
            return ""

    def type_text(self, text):
        if not text:
            return

        # 1. Copy text to clipboard
        try:
            subprocess.run(["wl-copy", text], check=True)
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return

        # 2. Small delay to ensure clipboard is populated
        time.sleep(0.05)

        # 3. Simulate Ctrl+V Pulse
        # Strategy A: pynput (Works for XWayland apps like Chrome/VSCode)
        try:
            with self.controller.pressed(keyboard.Key.ctrl):
                self.controller.press('v')
                self.controller.release('v')
            print("Pasted via pynput.")
        except Exception:
            # Strategy B: ydotool (Native Wayland virtual keyboard)
            try:
                # Keycodes: Ctrl (29), V (47)
                subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=True)
                print("Pasted via ydotool.")
            except Exception as e:
                print(f"Injection failed. Ensure ydotoold is running and you are in the 'input' group.")
