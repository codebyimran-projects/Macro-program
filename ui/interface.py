# ui/interface.py
import customtkinter as ctk  # type: ignore # Modern Tkinter library for beautiful UI
from core.macro_engine import MacroEngine  # Our macro engine to handle key-action mappings
import pyautogui  # type: ignore # Library to simulate keyboard typing
import subprocess  # To run programs or commands

# Modern UI class for MacroMaster-Pro
class MacroUI:
    def __init__(self):
        # ------------------ WINDOW SETUP ------------------
        self.window = ctk.CTk()  # Create the main window
        self.window.title("MacroMaster-Pro - CodeByImran")  # Window title
        self.window.geometry("950x650")  # Window size
        self.window.resizable(False, False)  # Disable resizing
        ctk.set_appearance_mode("dark")  # Set dark theme
        ctk.set_default_color_theme("green")  # Set accent color

        # ------------------ CORE ENGINE ------------------
        self.engine = MacroEngine()  # Initialize the macro engine

        # ------------------ HEADER ------------------
        self.header = ctk.CTkLabel(
            self.window,
            text="MacroMaster-Pro | CodeByImran",  # Header text
            font=("Arial", 24, "bold"),  # Font style
            text_color="#56b37f"  # Text color
        )
        self.header.pack(pady=(15, 5))  # Pack with vertical spacing

        # ------------------ INPUT FRAME ------------------
        self.input_frame = ctk.CTkFrame(self.window, corner_radius=10)  # Frame to hold input fields
        self.input_frame.pack(pady=15, padx=20, fill="x")  # Pack frame with padding and fill horizontally

        # Key input
        self.key_label = ctk.CTkLabel(self.input_frame, text="Macro Key:", anchor="w")  # Label for key
        self.key_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")  # Place in grid
        self.key_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. F1")  # Entry box for key
        self.key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")  # Fill horizontally

        # Action type selection
        self.action_label = ctk.CTkLabel(self.input_frame, text="Action Type:", anchor="w")  # Label
        self.action_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.action_var = ctk.StringVar(value="Type Text")  # Default value
        self.action_menu = ctk.CTkOptionMenu(
            self.input_frame,
            values=["Type Text", "Open App/Program", "Run Command", "Open Website"],  # Dropdown options
            variable=self.action_var  # Bind to variable
        )
        self.action_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Action input
        self.action_input_label = ctk.CTkLabel(self.input_frame, text="Action Value:", anchor="w")
        self.action_input_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.action_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Text, path, URL, or command")
        self.action_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Add Macro Button
        self.add_button = ctk.CTkButton(
            self.input_frame,
            text="Add Macro",  # Button text
            command=self.add_macro,  # Function called on click
            fg_color="#56b37f",  # Button color
            hover_color="#3d8b63"  # Hover color
        )
        self.add_button.grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")  # Span both columns

        # ------------------ MACRO LIST ------------------
        self.list_label = ctk.CTkLabel(self.window, text="Active Macros:", font=("Arial", 16))
        self.list_label.pack(pady=(10, 5))
        self.macro_listbox = ctk.CTkTextbox(self.window, height=250, width=900, corner_radius=10)
        self.macro_listbox.pack(pady=(0, 10))
        self.macro_listbox.configure(state="disabled")  # Disable editing

        # ------------------ CONTROL BUTTONS ------------------
        self.remove_button = ctk.CTkButton(
            self.window, text="Remove Macro by Key",
            command=self.remove_macro,  # Remove macro function
            fg_color="#ff4d4d",  # Red button
            hover_color="#cc0000"
        )
        self.remove_button.pack(pady=5, padx=20, fill="x")  # Fill horizontally

        # ------------------ FEEDBACK LABEL ------------------
        self.feedback_label = ctk.CTkLabel(self.window, text="", font=("Arial", 14))
        self.feedback_label.pack(pady=10)

        # ------------------ INITIAL UPDATE ------------------
        self.update_macro_list()  # Show initial macro list (empty at start)

    # ------------------ ADD MACRO ------------------
    def add_macro(self):
        key = self.key_entry.get().strip()  # Get key input
        action_type = self.action_var.get()  # Get selected action type
        value = self.action_entry.get().strip()  # Get action value input

        # Validate input
        if not key or not value:
            self.feedback_label.configure(text="⚠️ Please enter both key and action value!")
            return

        # Determine action based on type
        if action_type == "Type Text":
            def action(): pyautogui.write(value)  # Simulate typing text
        elif action_type == "Open App/Program":
            def action(): subprocess.Popen(value)  # Open program
        elif action_type == "Run Command":
            def action(): subprocess.run(value, shell=True)  # Run terminal command
        elif action_type == "Open Website":
            import webbrowser
            def action(): webbrowser.open(value)  # Open URL in default browser
        else:
            self.feedback_label.configure(text="⚠️ Unknown action type!")
            return

        # Add macro to engine
        self.engine.add_macro(key, action)
        self.feedback_label.configure(text=f"✅ Macro added: {key} -> {action_type}")
        self.key_entry.delete(0, "end")  # Clear key entry
        self.action_entry.delete(0, "end")  # Clear action entry
        self.update_macro_list()  # Refresh macro list

    # ------------------ REMOVE MACRO ------------------
    def remove_macro(self):
        key = self.key_entry.get().strip()  # Get key to remove
        if key in self.engine.list_macros():  # Check if macro exists
            self.engine.remove_macro(key)  # Remove macro
            self.feedback_label.configure(text=f"🗑️ Macro removed: {key}")
            self.key_entry.delete(0, "end")
            self.action_entry.delete(0, "end")
            self.update_macro_list()  # Refresh list
        else:
            self.feedback_label.configure(text="⚠️ Key not found in macros!")

    # ------------------ UPDATE MACRO LIST ------------------
    def update_macro_list(self):
        self.macro_listbox.configure(state="normal")  # Enable editing temporarily
        self.macro_listbox.delete("0.0", "end")  # Clear previous list
        macros = self.engine.list_macros()  # Get current macros
        if macros:
            for key, action in macros.items():
                self.macro_listbox.insert("end", f"{key} -> {action.__name__}\n")  # Show macro name
        else:
            self.macro_listbox.insert("end", "No macros added yet.")  # Empty list message
        self.macro_listbox.configure(state="disabled")  # Disable editing

    # ------------------ RUN APP ------------------
    def run(self):
        self.window.mainloop()  # Start the GUI loop
