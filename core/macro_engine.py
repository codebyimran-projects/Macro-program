# core/macro_engine.py
import pyautogui  # type: ignore # For simulating keyboard/mouse actions
import keyboard   # type: ignore # For listening to keyboard events and setting hotkeys

class MacroEngine:
    def __init__(self):
        """
        Initialize the Macro Engine.
        We use a dictionary to store macros in the format:
        {"key": function_to_execute_when_pressed}
        """
        self.macros = {}

    def add_macro(self, key, action):
        """
        Add a macro for a specific key.
        
        key: The keyboard key to trigger the macro (e.g., 'F1', 'a')
        action: The function that should run when the key is pressed
        
        This wrapper ensures:
        1. The original key is suppressed (so it won't type itself).
        2. The macro action runs only when the key is pressed.
        """

        # If a macro for this key already exists, remove it first
        if key in self.macros:
            self.remove_macro(key)

        # Wrapper function to suppress the key while executing the macro
        def wrapper():
            # Block the key temporarily to prevent default typing
            keyboard.block_key(key)
            # Execute the actual macro action
            action()
            # Unblock the key after action is done
            keyboard.unblock_key(key)

        # Store the wrapper in the macros dictionary
        self.macros[key] = wrapper

        # Register the hotkey with the keyboard listener
        # suppress=True ensures the key itself doesn't type in the current app
        keyboard.add_hotkey(key, wrapper, suppress=True)

    def remove_macro(self, key):
        """
        Remove a macro from the engine.
        It unregisters the key hotkey and deletes it from the dictionary.
        """
        if key in self.macros:
            keyboard.remove_hotkey(key)
            del self.macros[key]

    def list_macros(self):
        """
        Return the current macros dictionary.
        Key = assigned key
        Value = wrapper function
        """
        return self.macros
