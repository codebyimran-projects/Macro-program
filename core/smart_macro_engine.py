# core/smart_macro_engine.py
import pyautogui  # type: ignore
import keyboard   # type: ignore
import threading
import time

class SmartMacroEngine:
    def __init__(self):
        """
        Smart Macro Engine:
        - macros: list of dicts {condition, text, delay_char, delay_word}
        - buffer: stores recent pressed keys
        """
        self.macros = []
        self.buffer = []
        self.lock = threading.Lock()
        self.current_thread = None

        # Listen to all key presses to update buffer
        keyboard.on_press(self.key_pressed)

    def key_pressed(self, event):
        """Update buffer on key press and check macros"""
        key = event.name
        if len(key) == 1:  # only normal keys
            self.buffer.append(key)
            # keep buffer length reasonable
            if len(self.buffer) > 10:
                self.buffer.pop(0)
            self.trigger_macros()

    def add_macro(self, condition_func, text, delay_char=0, delay_word=0):
        """Add a macro with a condition function"""
        macro = {
            "condition": condition_func,
            "text": text,
            "delay_char": delay_char,
            "delay_word": delay_word
        }
        self.macros.append(macro)

    def trigger_macros(self):
        """Check all macros and run the first that matches"""
        with self.lock:
            for macro in self.macros:
                if macro["condition"](self.buffer):
                    # Stop previous typing
                    if self.current_thread and self.current_thread.is_alive():
                        self.buffer.clear()
                    # Start typing in a new thread
                    self.current_thread = threading.Thread(target=self.type_macro, args=(macro,))
                    self.current_thread.start()
                    break  # trigger only one at a time

    def type_macro(self, macro):
        """Type the text with character and word delays"""
        text = macro["text"]
        delay_char = macro["delay_char"]
        delay_word = macro["delay_word"]

        words = text.split(" ")
        for word in words:
            for char in word:
                # If buffer changed mid-way, stop typing
                if not macro["condition"](self.buffer):
                    return
                pyautogui.write(char)
                time.sleep(delay_char)
            pyautogui.write(" ")
            time.sleep(delay_word)
