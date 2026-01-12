from pynput import keyboard

class Typer:
    def __init__(self):
        self.controller = keyboard.Controller()

    def type_text(self, text):
        if not text:
            return
        self.controller.type(text)
