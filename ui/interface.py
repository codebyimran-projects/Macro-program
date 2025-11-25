# ui/interface.py
import customtkinter as ctk
from core.smart_macro_engine import SmartMacroEngine
import threading
import tkinter as tk
from tkinter import messagebox


class MacroUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.window = ctk.CTk()
        self.window.title("MacroMaster-Pro | Code by Imran")
        self.window.geometry("1250x800")  # Increased width for new column

        self.engine = SmartMacroEngine()

        # Header
        self.header = ctk.CTkLabel(self.window, text="MacroMaster-Pro | Code by Imran", font=("Arial", 24, "bold"))
        self.header.pack(pady=12)

        # Table frame with scrollbar
        self.table_container = ctk.CTkFrame(self.window)
        self.table_container.pack(padx=12, pady=6, fill="both", expand=True)

        # Create canvas and scrollbar for table
        self.canvas = tk.Canvas(self.table_container, bg='#2b2b2b', highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.table_container, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Table headers - ADDED PER-CHAR DELAYS COLUMN
        headers = ["Keys / Sequence", "Output", "Timeout", "CharDelay", "WordDelay", "Per-Char Delays", "Delete"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.scrollable_frame, text=h, font=("Arial", 12, "bold")).grid(
                row=0, column=i, padx=6, pady=6, sticky="ew"
            )

        self.row_widgets = []

        # Input area
        self.add_frame = ctk.CTkFrame(self.window)
        self.add_frame.pack(padx=12, pady=8, fill="x")

        # Basic single-rule inputs - ADDED PER-CHAR DELAYS FIELD
        self.keys_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Keys (e.g. i or i+b)", width=150)
        self.keys_entry.grid(row=0, column=0, padx=6)

        self.output_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Output text", width=150)
        self.output_entry.grid(row=0, column=1, padx=6)

        self.timeout_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Timeout (sec)", width=100)
        self.timeout_entry.insert(0, "1.0")
        self.timeout_entry.grid(row=0, column=2, padx=6)

        self.char_delay_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Char Delay (sec)", width=100)
        self.char_delay_entry.insert(0, "0.02")
        self.char_delay_entry.grid(row=0, column=3, padx=6)

        self.word_delay_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Word Delay (sec)", width=100)
        self.word_delay_entry.insert(0, "0.15")
        self.word_delay_entry.grid(row=0, column=4, padx=6)

        # NEW: Per-char delays entry
        self.per_char_delays_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Per-Char Delays (i:0.1 m:1.0)", width=200)
        self.per_char_delays_entry.grid(row=0, column=5, padx=6)

        self.add_btn = ctk.CTkButton(self.add_frame, text="Add Rule", command=self.add_rule_from_inputs)
        self.add_btn.grid(row=0, column=6, padx=6)

        # Separator
        self.sep = ctk.CTkLabel(self.window, text="— OR — Bulk Import Using Logic Syntax —", font=("Arial", 12))
        self.sep.pack(pady=4)

        # Logic input
        self.logic_frame = ctk.CTkFrame(self.window)
        self.logic_frame.pack(padx=12, pady=6, fill="both", expand=False)

        self.logic_label = ctk.CTkLabel(self.logic_frame, text="Logic (multiple clauses):", anchor="w")
        self.logic_label.grid(row=0, column=0, sticky="w", padx=6, pady=4, columnspan=4)

        self.logic_text = ctk.CTkTextbox(self.logic_frame, width=1100, height=120)
        example = (
            "# Multiple formats supported:\n"
            "if i { imran, 0.02, 0.1, 1.0 }\n"
            "if i+b { khan, 0.02, 0.15, 1.0 }\n"
            "i+c = xyz\n"
            "i+d: hello world\n"
            "# NEW: Per-character delays using | separator:\n"
            "if t { test | t:0.5 e:1.0 s:0.2 }\n"
            "i = imran | i:0.1 m:1.0 r:0.05 a:0.2 n:0.3\n"
            "b+c = khan | k:0.5 h:0.1 a:2.0 n:0.05"
        )
        self.logic_text.insert("0.0", example)
        self.logic_text.grid(row=1, column=0, columnspan=4, padx=6, pady=6)

        # Default time/delays for logic parsing
        self.logic_timeout_entry = ctk.CTkEntry(self.logic_frame, placeholder_text="Default Timeout (sec)", width=140)
        self.logic_timeout_entry.insert(0, "1.0")
        self.logic_timeout_entry.grid(row=2, column=0, padx=6, pady=6)

        self.logic_char_delay_entry = ctk.CTkEntry(self.logic_frame, placeholder_text="Default Char Delay", width=140)
        self.logic_char_delay_entry.insert(0, "0.02")
        self.logic_char_delay_entry.grid(row=2, column=1, padx=6, pady=6)

        self.logic_word_delay_entry = ctk.CTkEntry(self.logic_frame, placeholder_text="Default Word Delay", width=140)
        self.logic_word_delay_entry.insert(0, "0.15")
        self.logic_word_delay_entry.grid(row=2, column=2, padx=6, pady=6)

        self.add_logic_btn = ctk.CTkButton(self.logic_frame, text="Add Logic Clauses", command=self.add_logic_clauses)
        self.add_logic_btn.grid(row=2, column=3, padx=6, pady=6)

        # Status label
        self.status_label = ctk.CTkLabel(self.window, text="Ready - 0 rules loaded", text_color="lightblue")
        self.status_label.pack(pady=4)

        # Control buttons
        self.controls_frame = ctk.CTkFrame(self.window)
        self.controls_frame.pack(padx=12, pady=6, fill="x")

        self.clear_btn = ctk.CTkButton(self.controls_frame, text="Clear All Rules", command=self.clear_rules, fg_color="red")
        self.clear_btn.grid(row=0, column=0, padx=6)

        self.refresh_btn = ctk.CTkButton(self.controls_frame, text="Refresh Table", command=self.update_table)
        self.refresh_btn.grid(row=0, column=1, padx=6)

   

        # initial table
        self.update_table()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # ---------------------------
    # UI actions
    # ---------------------------
    def add_rule_from_inputs(self):
        keys_raw = self.keys_entry.get().strip()
        output = self.output_entry.get().strip()
        per_char_delays = self.per_char_delays_entry.get().strip() or None
        
        try:
            timeout = float(self.timeout_entry.get())
        except Exception:
            timeout = 1.0
        try:
            char_delay = float(self.char_delay_entry.get())
        except Exception:
            char_delay = 0.02
        try:
            word_delay = float(self.word_delay_entry.get())
        except Exception:
            word_delay = 0.15

        if not keys_raw or not output:
            messagebox.showwarning("Input Error", "Please enter both keys and output")
            return

        keys = self._parse_keys_input(keys_raw)
        try:
            self.engine.add_rule(keys, output, timeout, char_delay, word_delay, per_char_delays)
            self.update_table()
            # Clear input fields
            self.keys_entry.delete(0, 'end')
            self.output_entry.delete(0, 'end')
            self.per_char_delays_entry.delete(0, 'end')
        except ValueError as e:
            messagebox.showerror("Duplicate Rule", str(e))

    def add_logic_clauses(self):
        logic_text = self.logic_text.get("0.0", "end").strip()
        if not logic_text:
            messagebox.showwarning("Input Error", "Please enter logic clauses")
            return
            
        try:
            timeout = float(self.logic_timeout_entry.get())
        except:
            timeout = 1.0
        try:
            char_delay = float(self.logic_char_delay_entry.get())
        except:
            char_delay = 0.02
        try:
            word_delay = float(self.logic_word_delay_entry.get())
        except:
            word_delay = 0.15

        # Show processing message
        self.status_label.configure(text="Processing logic clauses...")
        
        # Use a thread so UI doesn't freeze
        threading.Thread(target=self._add_logic_thread, args=(logic_text, timeout, char_delay, word_delay), daemon=True).start()

    def _add_logic_thread(self, logic_text, timeout, char_delay, word_delay):
        try:
            rules_added = self.engine.add_rules_from_logic(logic_text, timeout, char_delay, word_delay)
            self.window.after(0, self._on_logic_complete, rules_added)
        except Exception as e:
            self.window.after(0, self._on_logic_error, str(e))

    def _on_logic_complete(self, rules_added):
        self.update_table()
        self.status_label.configure(text=f"Successfully added {rules_added} rules - Total: {self.engine.get_rules_count()}")

    def _on_logic_error(self, error_msg):
        messagebox.showerror("Processing Error", f"Error processing logic: {error_msg}")
        self.status_label.configure(text=f"Error - {self.engine.get_rules_count()} rules loaded")

    def _parse_keys_input(self, keys_raw: str):
        s = keys_raw.replace(",", "+").replace(" ", "+")
        parts = [p.strip().lower() for p in s.split("+") if p.strip()]
        return parts

    def update_table(self):
        # remove old widgets
        for row in self.row_widgets:
            for w in row:
                try:
                    w.destroy()
                except Exception:
                    pass
        self.row_widgets.clear()

        # repopulate
        rules = self.engine.debug_rules()
        for i, r in enumerate(rules):
            row = []
            
            k_label = ctk.CTkLabel(self.scrollable_frame, text="+".join(r["keys"]))
            k_label.grid(row=i+1, column=0, padx=6, pady=4, sticky="ew")
            row.append(k_label)

            o_label = ctk.CTkLabel(self.scrollable_frame, text=r["output"])
            o_label.grid(row=i+1, column=1, padx=6, pady=4, sticky="ew")
            row.append(o_label)

            t_label = ctk.CTkLabel(self.scrollable_frame, text=f"{r['timeout']:.2f}")
            t_label.grid(row=i+1, column=2, padx=6, pady=4, sticky="ew")
            row.append(t_label)

            cd_label = ctk.CTkLabel(self.scrollable_frame, text=f"{r['char_delay']:.3f}")
            cd_label.grid(row=i+1, column=3, padx=6, pady=4, sticky="ew")
            row.append(cd_label)

            wd_label = ctk.CTkLabel(self.scrollable_frame, text=f"{r['word_delay']:.3f}")
            wd_label.grid(row=i+1, column=4, padx=6, pady=4, sticky="ew")
            row.append(wd_label)

            # NEW: Per-char delays display
            per_char_text = ""
            if r.get("per_char_delays"):
                per_char_text = ", ".join([f"{k}:{v}" for k, v in r["per_char_delays"].items()])
            pcd_label = ctk.CTkLabel(self.scrollable_frame, text=per_char_text, wraplength=200)
            pcd_label.grid(row=i+1, column=5, padx=6, pady=4, sticky="ew")
            row.append(pcd_label)

            del_btn = ctk.CTkButton(self.scrollable_frame, text="Delete", 
                                  command=lambda rule=r: self._delete_rule_by_repr(rule),
                                  fg_color="red", hover_color="darkred")
            del_btn.grid(row=i+1, column=6, padx=6, pady=4)
            row.append(del_btn)

            self.row_widgets.append(row)

        # Update status
        self.status_label.configure(text=f"Ready - {len(rules)} rules loaded")

    def _delete_rule_by_repr(self, rule_repr):
        # find matching rule object from engine.rules and remove
        for r in list(self.engine.rules):
            if (r["keys"] == rule_repr["keys"] and 
                r["output"] == rule_repr["output"] and 
                float(r["timeout"]) == float(rule_repr["timeout"])):
                self.engine.rules.remove(r)
                break
        self.update_table()

    def clear_rules(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all rules?"):
            self.engine.clear_rules()
            self.update_table()

    def export_rules(self):
        """Export current rules to logic format"""
        rules_text = ""
        for rule in self.engine.debug_rules():
            base_rule = f"if {'+'.join(rule['keys'])} {{ {rule['output']}, {rule['char_delay']}, {rule['word_delay']}, {rule['timeout']} }}"
            
            if rule.get("per_char_delays"):
                delays_str = " ".join([f"{k}:{v}" for k, v in rule["per_char_delays"].items()])
                rules_text += f"{base_rule} | {delays_str}\n"
            else:
                rules_text += f"{base_rule}\n"
        
        # Create export window
        export_window = ctk.CTkToplevel(self.window)
        export_window.title("Export Rules")
        export_window.geometry("600x400")
        
        textbox = ctk.CTkTextbox(export_window, width=580, height=350)
        textbox.insert("0.0", rules_text)
        textbox.pack(padx=10, pady=10)
        
        close_btn = ctk.CTkButton(export_window, text="Close", command=export_window.destroy)
        close_btn.pack(pady=10)

    def run(self):
        self.window.mainloop()