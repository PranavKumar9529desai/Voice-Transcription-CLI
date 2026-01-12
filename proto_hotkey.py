from pynput import keyboard
import time

# Controller for typing text
controller = keyboard.Controller()

def on_press(key):
    try:
        # Check for specific key (e.g., F8 or Right Control)
        if key == keyboard.Key.f8:
            print("F8 pressed - Start recording logic...")
        elif hasattr(key, 'char') and key.char == 'q':
            print("Exiting...")
            return False # Stop listener
    except AttributeError:
        pass

def on_release(key):
    if key == keyboard.Key.f8:
        print("F8 released - Stop recording, transcribe, and type...")
        # Simulate typing
        text_to_type = " (transcribed text)"
        controller.type(text_to_type)

print("Starting PTT prototype (Press holding F8, then release. Press 'q' to exit.)")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
