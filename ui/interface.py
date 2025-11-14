# ui/interface.py
import customtkinter as ctk
from core.smart_macro_engine import SmartMacroEngine
from tkinter import messagebox

class MacroUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("MacroMaster-Pro | CodeByImran")
        self.window.geometry("1100x750")
        self.window.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # ---------------- CORE ENGINE ----------------
        self.engine = SmartMacroEngine()

        # ---------------- HEADER ----------------
        self.header = ctk.CTkLabel(
            self.window, text="MacroMaster-Pro | CodeByImran",
            font=("Arial", 26, "bold"), text_color="#56b37f"
        )
        self.header.pack(pady=10)

        # ---------------- MACRO TABLE ----------------
        self.table_frame = ctk.CTkFrame(self.window)
        self.table_frame.pack(pady=10, padx=20, fill="x")
        headers = ["Keys/Sequence", "Text", "Delay Char", "Delay Word", "Condition"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.table_frame, text=h, font=("Arial", 14, "bold")).grid(row=0, column=i, padx=10)
        self.macro_rows = []

        # ---------------- ADD MACRO ----------------
        self.add_frame = ctk.CTkFrame(self.window)
        self.add_frame.pack(pady=20, padx=20, fill="x")

        self.key_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Keys e.g. i or i+b")
        self.key_entry.grid(row=0, column=0, padx=5, pady=5)
        self.text_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Text to type")
        self.text_entry.grid(row=0, column=1, padx=5, pady=5)
        self.delay_char_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Delay Char (sec)")
        self.delay_char_entry.grid(row=0, column=2, padx=5, pady=5)
        self.delay_word_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Delay Word (sec)")
        self.delay_word_entry.grid(row=0, column=3, padx=5, pady=5)

        self.add_button = ctk.CTkButton(self.add_frame, text="Add Macro", command=self.add_macro)
        self.add_button.grid(row=0, column=4, padx=10, pady=5)

        # ---------------- FEEDBACK ----------------
        self.feedback_label = ctk.CTkLabel(self.window, text="", font=("Arial", 14))
        self.feedback_label.pack(pady=10)

    # ---------------- ADD MACRO ----------------
    def add_macro(self):
        keys = self.key_entry.get().strip().split("+")
        text = self.text_entry.get().strip()
        try: delay_char = float(self.delay_char_entry.get())
        except: delay_char = 0
        try: delay_word = float(self.delay_word_entry.get())
        except: delay_word = 0

        if not keys or not text:
            self.feedback_label.configure(text="⚠️ Fill keys and text!")
            return

        # Create condition function
        def condition(buf, k=keys):
            return buf[-len(k):] == k  # matches the end of buffer

        self.engine.add_macro(condition, text, delay_char, delay_word)
        self.feedback_label.configure(text=f"✅ Macro added: {'+'.join(keys)} -> {text}")
        self.update_macro_table()

    # ---------------- UPDATE TABLE ----------------
    def update_macro_table(self):
        for row in self.macro_rows:
            for w in row:
                w.destroy()
        self.macro_rows.clear()

        for i, macro in enumerate(self.engine.macros):
            row_widgets = []
            keys_label = ctk.CTkLabel(self.table_frame, text="+".join(macro["condition"].__defaults__[0]))
            keys_label.grid(row=i+1, column=0, padx=10)
            row_widgets.append(keys_label)

            text_label = ctk.CTkLabel(self.table_frame, text=macro["text"])
            text_label.grid(row=i+1, column=1, padx=10)
            row_widgets.append(text_label)

            delay_char_label = ctk.CTkLabel(self.table_frame, text=str(macro["delay_char"]))
            delay_char_label.grid(row=i+1, column=2, padx=10)
            row_widgets.append(delay_char_label)

            delay_word_label = ctk.CTkLabel(self.table_frame, text=str(macro["delay_word"]))
            delay_word_label.grid(row=i+1, column=3, padx=10)
            row_widgets.append(delay_word_label)

            cond_label = ctk.CTkLabel(self.table_frame, text="End of Buffer Match")
            cond_label.grid(row=i+1, column=4, padx=10)
            row_widgets.append(cond_label)

            self.macro_rows.append(row_widgets)

    # ---------------- RUN APP ----------------
    def run(self):
        self.window.mainloop()
