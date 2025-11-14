# ui/interface.py
import customtkinter as ctk  # type: ignore
from core.macro_engine import MacroEngine
import pyautogui  # type: ignore
import subprocess
import webbrowser
import uuid

"""
UI: table-like layout using CustomTkinter frames.
Supports adding:
- Single/combo macros (trigger in 'Key' field)
- Sequence macros (select 'Sequence' and enter 'a,b' in Sequence Keys)
- Delay before execution and char delay for slow typing
"""

class MacroUI:
    def __init__(self):
        # Window setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.window = ctk.CTk()
        self.window.title("MacroMaster-Pro - CodeByImran")
        self.window.geometry("1000x700")
        self.window.resizable(False, False)

        # Engine
        self.engine = MacroEngine()

        # Header
        header = ctk.CTkLabel(self.window, text="MacroMaster-Pro | CodeByImran", font=("Arial", 22, "bold"))
        header.pack(pady=(12, 8))

        # Top frame for inputs
        top_frame = ctk.CTkFrame(self.window, corner_radius=8)
        top_frame.pack(fill="x", padx=12, pady=(0, 12))

        # Key / trigger
        ctk.CTkLabel(top_frame, text="Key / Trigger:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.key_entry = ctk.CTkEntry(top_frame, placeholder_text="e.g. a  or ctrl+shift+a")
        self.key_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        # Action type
        ctk.CTkLabel(top_frame, text="Action Type:").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.action_var = ctk.StringVar(value="Type Text")
        self.action_menu = ctk.CTkOptionMenu(top_frame, values=["Type Text", "Open App/Program", "Run Command", "Open Website", "Sequence"], variable=self.action_var)
        self.action_menu.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

        # Action value (for text/path/URL)
        ctk.CTkLabel(top_frame, text="Action Value:").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.action_entry = ctk.CTkEntry(top_frame, placeholder_text="Text, path, URL, or command")
        self.action_entry.grid(row=1, column=1, padx=8, pady=8, sticky="ew")

        # Sequence keys input (only used when Action Type == Sequence)
        ctk.CTkLabel(top_frame, text="Sequence Keys:").grid(row=1, column=2, padx=8, pady=8, sticky="w")
        self.sequence_entry = ctk.CTkEntry(top_frame, placeholder_text="e.g. i,b  (first,second)")
        self.sequence_entry.grid(row=1, column=3, padx=8, pady=8, sticky="ew")

        # Delay before execution and char delay
        ctk.CTkLabel(top_frame, text="Delay (sec):").grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.delay_entry = ctk.CTkEntry(top_frame, placeholder_text="0")
        self.delay_entry.grid(row=2, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(top_frame, text="Char delay (sec):").grid(row=2, column=2, padx=8, pady=8, sticky="w")
        self.char_delay_entry = ctk.CTkEntry(top_frame, placeholder_text="0 (slow typing)")
        self.char_delay_entry.grid(row=2, column=3, padx=8, pady=8, sticky="ew")

        # Sequence window (seconds)
        ctk.CTkLabel(top_frame, text="Seq Window (s):").grid(row=3, column=0, padx=8, pady=8, sticky="w")
        self.seq_window_entry = ctk.CTkEntry(top_frame, placeholder_text="1.0")
        self.seq_window_entry.grid(row=3, column=1, padx=8, pady=8, sticky="ew")

        # Add button
        self.add_btn = ctk.CTkButton(top_frame, text="Add Macro", command=self.gui_add_macro, fg_color="#56b37f")
        self.add_btn.grid(row=3, column=3, padx=8, pady=10, sticky="ew")

        # Expand columns for layout
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(3, weight=1)

        # ---------------- Table area ----------------
        table_frame = ctk.CTkFrame(self.window, corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Table header
        headers = ["ID", "Trigger", "Type", "Value", "Delay", "CharDelay", "Sequence", "Window", "Edit", "Delete"]
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(table_frame, text=h, anchor="w", width=1)
            lbl.grid(row=0, column=i, padx=6, pady=6, sticky="w")

        # container for rows (we'll rebuild rows)
        self.table_frame_inner = ctk.CTkFrame(table_frame)
        self.table_frame_inner.grid(row=1, column=0, columnspan=len(headers), sticky="nsew", padx=6, pady=6)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(len(headers)-1, weight=1)

        # store row widgets for update/removal
        self._row_widgets = {}

        # initial refresh
        self.refresh_table()

    # ---------- GUI add macro (reads fields and calls engine.add_macro) ----------
    def gui_add_macro(self):
        trigger = self.key_entry.get().strip()
        atype = self.action_var.get()
        value = self.action_entry.get().strip()
        seq_text = self.sequence_entry.get().strip()
        try:
            delay = float(self.delay_entry.get().strip() or 0)
        except ValueError:
            self._flash_feedback("Invalid delay value")
            return
        try:
            char_delay = float(self.char_delay_entry.get().strip() or 0)
        except ValueError:
            self._flash_feedback("Invalid char delay value")
            return
        try:
            seq_window = float(self.seq_window_entry.get().strip() or 1.0)
        except ValueError:
            seq_window = 1.0

        # build macro_id
        macro_id = str(uuid.uuid4())[:8]

        if atype == "Sequence":
            # parse sequence keys like 'i,b' -> ['i','b']
            parts = [p.strip() for p in seq_text.split(",") if p.strip()]
            if len(parts) != 2:
                self._flash_feedback("Sequence requires two keys like 'i,b'")
                return
            sequence = parts
            # For sequence macros, trigger (hotkey) isn't used the same way. We'll still register handlers for both keys.
            # value is used as the action text/path/command as usual.
            self.engine.add_macro(macro_id, trigger=None, mtype="sequence", value=value,
                                  delay_before=delay, char_delay=char_delay,
                                  sequence=sequence, window=seq_window)
        else:
            # For single/combo actions, trigger must be provided
            if not trigger:
                self._flash_feedback("Trigger required for single/combo macros")
                return

            # create action according to type: we will have engine choose default typing if value looks like URL etc.
            # Here we help detect web URLs or choose proper action binding by making action string sensible.
            # We pass trigger as provided.
            self.engine.add_macro(macro_id, trigger=trigger, mtype="single", value=value,
                                  delay_before=delay, char_delay=char_delay, sequence=None, window=seq_window)

        # clear inputs
        self.key_entry.delete(0, "end")
        self.action_entry.delete(0, "end")
        self.sequence_entry.delete(0, "end")

        self._flash_feedback("Macro added")
        self.refresh_table()

    # ---------- Remove macro by id ----------
    def gui_remove_macro(self, macro_id: str):
        self.engine.remove_macro(macro_id)
        self._flash_feedback("Macro removed")
        self.refresh_table()

    # ---------- Edit macro (basic: re-open fields filled) ----------
    def gui_edit_macro(self, macro_id: str):
        # fetch macro details and populate top inputs for user to modify then remove old macro
        macros = self.engine.list_macros()
        mac = macros.get(macro_id)
        if not mac:
            self._flash_feedback("Macro not found")
            return
        # populate fields
        trig = mac.get("trigger") or ""
        self.key_entry.delete(0, "end"); self.key_entry.insert(0, trig)
        self.action_entry.delete(0, "end"); self.action_entry.insert(0, mac.get("value") or "")
        if mac.get("sequence"):
            self.action_var.set("Sequence")
            seq = ",".join(mac.get("sequence"))
            self.sequence_entry.delete(0, "end"); self.sequence_entry.insert(0, seq)
        else:
            self.action_var.set("Type Text")
            self.sequence_entry.delete(0, "end")
        self.delay_entry.delete(0, "end"); self.delay_entry.insert(0, str(mac.get("delay_before", 0)))
        self.char_delay_entry.delete(0, "end"); self.char_delay_entry.insert(0, str(mac.get("char_delay", 0)))
        self.seq_window_entry.delete(0, "end"); self.seq_window_entry.insert(0, str(mac.get("window", 1.0)))

        # remove old macro so user can add updated one
        self.engine.remove_macro(macro_id)
        self._flash_feedback("Edit mode: change fields and press Add Macro")

    # ---------- utility to show brief message ----------
    def _flash_feedback(self, text: str):
        self._tmp_feedback = text
        # show permanently in this version
        # (You can implement timed clear if desired)
        # We'll use a label in header area; for simplicity we reuse window.title suffix
        # But we also can show ctk label; here we change window title briefly:
        self.window.title(f"MacroMaster-Pro - {text}")

    # ---------- refresh table rows ----------
    def refresh_table(self):
        # remove old row widgets
        for w in self.table_frame_inner.winfo_children():
            w.destroy()

        macros = self.engine.list_macros()
        # macros is dict macro_id -> info dict
        for r, (mid, info) in enumerate(macros.items()):
            # columns: ID, Trigger, Type, Value, Delay, CharDelay, Sequence, Window, Edit, Delete
            c = 0
            ctk.CTkLabel(self.table_frame_inner, text=mid).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            ctk.CTkLabel(self.table_frame_inner, text=str(info.get("trigger") or "")).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            ctk.CTkLabel(self.table_frame_inner, text=str(info.get("type") or "")).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            ctk.CTkLabel(self.table_frame_inner, text=str(info.get("value") or "")).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            ctk.CTkLabel(self.table_frame_inner, text=str(info.get("delay_before") or 0)).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            ctk.CTkLabel(self.table_frame_inner, text=str(info.get("char_delay") or 0)).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            seq = info.get("sequence") or ""
            if isinstance(seq, list):
                seq = ",".join(seq)
            ctk.CTkLabel(self.table_frame_inner, text=str(seq)).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1
            ctk.CTkLabel(self.table_frame_inner, text=str(info.get("window") or 0)).grid(row=r, column=c, padx=6, pady=6, sticky="w"); c += 1

            # Edit button
            edit_btn = ctk.CTkButton(self.table_frame_inner, text="Edit", width=60, command=lambda m=mid: self.gui_edit_macro(m))
            edit_btn.grid(row=r, column=c, padx=6, pady=6); c += 1
            # Delete button
            del_btn = ctk.CTkButton(self.table_frame_inner, text="Delete", width=60, fg_color="#ff4d4d",
                                     command=lambda m=mid: self.gui_remove_macro(m))
            del_btn.grid(row=r, column=c, padx=6, pady=6)

    # ---------- start UI loop ----------
    def run(self):
        self.window.mainloop()
