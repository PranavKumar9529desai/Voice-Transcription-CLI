import os
import subprocess
import time

from pynput import keyboard

# List of known terminal applications that typically require Ctrl+Shift+V
# Note: "dev.zed.Zed" is ambiguous (Editor vs Terminal), so we don't force it here.
# Users should use the Shift-Override for Zed's terminal.
TERMINAL_APPS = {
    "gnome-terminal-server",
    "Gnome-terminal",
    "dev.zed.Zed",
}


class Typer:
    def __init__(self):
        self.controller = keyboard.Controller()
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
        print(f"Typer initialized for session: {self.session_type}")

    def type_text(self, text, force_terminal=False):
        """
        Inject text into the active window.

        Args:
            text (str): The text to type.
            force_terminal (bool): If True, forces Ctrl+Shift+V (for Zed/Terminals).
        """
        if not text:
            return

        if self.session_type == "wayland":
            self._type_wayland(text, force_terminal)
        else:
            self._type_x11(text, force_terminal)

    def _get_active_window_class(self):
        """Get the class name of the active window using xdotool."""
        try:
            # Get active window ID
            window_id = subprocess.check_output(
                ["xdotool", "getactivewindow"], text=True
            ).strip()

            # Get window class name
            window_class = subprocess.check_output(
                ["xdotool", "getwindowclassname", window_id], text=True
            ).strip()
            return window_class
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _type_x11(self, text, force_terminal):
        """X11 implementation using xclip and xdotool."""
        try:
            # 1. Copy to selection (primary) and clipboard
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=text, text=True, check=True
            )

            # 2. Small delay
            time.sleep(0.05)

            # 3. Determine Paste Strategy
            paste_keys = "ctrl+v"

            # Check 1: Manual Override
            if force_terminal:
                print("Paste Strategy: Manual Override -> Ctrl+Shift+V")
                paste_keys = "ctrl+shift+v"
            else:
                # Check 2: Auto-Detection
                active_class = self._get_active_window_class()
                if active_class in TERMINAL_APPS:
                    print(
                        f"Paste Strategy: Detected Terminal ({active_class}) -> Ctrl+Shift+V"
                    )
                    paste_keys = "ctrl+shift+v"
                else:
                    print(
                        f"Paste Strategy: Default ({active_class or 'Unknown'}) -> Ctrl+V"
                    )

            # 4. Paste using xdotool
            subprocess.run(["xdotool", "key", paste_keys], check=True)

        except FileNotFoundError:
            print(
                "Error: 'xclip' or 'xdotool' not found. Please install them: sudo apt install xclip xdotool"
            )
            self._fallback_pynput_paste(force_terminal)
        except Exception as e:
            print(f"X11 Injection failed: {e}")
            self._fallback_pynput_paste(force_terminal)

    def _type_wayland(self, text, force_terminal):
        """Wayland implementation using wl-copy and ydotool."""
        try:
            subprocess.run(["wl-copy", text], check=True)
            time.sleep(0.05)

            try:
                if force_terminal:
                    # Ctrl (29), Shift (42), V (47)
                    subprocess.run(
                        [
                            "ydotool",
                            "key",
                            "29:1",
                            "42:1",
                            "47:1",
                            "47:0",
                            "42:0",
                            "29:0",
                        ],
                        check=True,
                        capture_output=True,
                    )
                else:
                    # Ctrl (29), V (47)
                    subprocess.run(
                        ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"],
                        check=True,
                        capture_output=True,
                    )
                print("Pasted via ydotool.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._fallback_pynput_paste(force_terminal)
        except FileNotFoundError:
            print("Error: 'wl-clipboard' not found. Please install it.")
        except Exception as e:
            print(f"Wayland Injection failed: {e}")

    def _fallback_pynput_paste(self, force_terminal):
        """Standard pynput fallback."""
        try:
            with self.controller.pressed(keyboard.Key.ctrl):
                if force_terminal:
                    with self.controller.pressed(keyboard.Key.shift):
                        self.controller.press("v")
                        self.controller.release("v")
                else:
                    self.controller.press("v")
                    self.controller.release("v")
            print("Pasted via pynput fallback.")
        except Exception as e:
            print(f"Fallback paste failed: {e}")
