# core/smart_macro_engine.py
import pyautogui
import keyboard
import threading
import time
import re

class SmartMacroEngine:
    def __init__(self):
        self.rules = []  # List of macros
        self.buffer = []  # Pressed keys
        self.buffer_time = []  # Timestamps
        self.lock = threading.Lock()
        self.is_typing = False
        self.lookahead_timer = None
        self.active_timers = []

        # Start keyboard listener
        threading.Thread(target=self._keyboard_listener, daemon=True).start()

    # -------------------------
    # Add a macro
    # -------------------------
    def add_rule(self, keys, output, timeout=1.0, char_delay=0.02, word_delay=0.15):
        keys = [k.lower() for k in keys]
        for rule in self.rules:
            if rule["keys"] == keys:
                raise ValueError(f"Sequence '{'+'.join(keys)}' already exists!")
        self.rules.append({
            "keys": keys,
            "output": output,
            "timeout": timeout,
            "char_delay": char_delay,
            "word_delay": word_delay
        })

    # -------------------------
    # Enhanced logic parser with multiple formats
    # -------------------------
    def add_rules_from_logic(self, logic_text, default_timeout=1.0, default_char_delay=0.02, default_word_delay=0.15):
        """
        Parse multiple logic formats:
        Format 1: if <keys> { <output>, <char_delay>, <word_delay>, <timeout> }
        Format 2: if <keys> { <output> }
        Format 3: <keys> = <output>
        Format 4: <keys>: <output>
        """
        lines = [l.strip() for l in logic_text.split("\n") if l.strip()]
        rules_added = 0
        
        for line in lines:
            try:
                # Skip comment lines
                if line.startswith("#") or line.startswith("//"):
                    continue
                    
                # Format 1 & 2: if <keys> { <output>, <char_delay>, <word_delay>, <timeout> }
                if line.lower().startswith("if") and "{" in line and "}" in line:
                    self._parse_if_format(line, default_timeout, default_char_delay, default_word_delay)
                    rules_added += 1
                
                # Format 3: <keys> = <output>
                elif "=" in line and not line.startswith("if"):
                    self._parse_equals_format(line, default_timeout, default_char_delay, default_word_delay)
                    rules_added += 1
                
                # Format 4: <keys>: <output>
                elif ":" in line and not line.startswith("if"):
                    self._parse_colon_format(line, default_timeout, default_char_delay, default_word_delay)
                    rules_added += 1
                    
            except Exception as e:
                print(f"Error parsing line: {line} - {e}")
                continue
                
        return rules_added

    def _parse_if_format(self, line, default_timeout, default_char_delay, default_word_delay):
        """Parse if <keys> { <output>, <char_delay>, <word_delay>, <timeout> } format"""
        try:
            # Extract keys part
            keys_part = line.split("if", 1)[1].split("{")[0].strip()
            # Extract content inside braces
            content = line.split("{", 1)[1].rsplit("}", 1)[0].strip()
            
            # Parse content which may contain output and parameters
            parts = [p.strip() for p in content.split(",")]
            output = parts[0].strip()
            
            # Use defaults or override with provided values
            char_delay = default_char_delay
            word_delay = default_word_delay
            timeout = default_timeout
            
            if len(parts) > 1:
                try:
                    char_delay = float(parts[1])
                except ValueError:
                    pass
            if len(parts) > 2:
                try:
                    word_delay = float(parts[2])
                except ValueError:
                    pass
            if len(parts) > 3:
                try:
                    timeout = float(parts[3])
                except ValueError:
                    pass
            
            keys = [k.strip().lower() for k in keys_part.replace("+", " ").split()]
            if keys and output:
                self.add_rule(keys, output, timeout, char_delay, word_delay)
        except Exception as e:
            print(f"Error parsing if format: {line} - {e}")

    def _parse_equals_format(self, line, default_timeout, default_char_delay, default_word_delay):
        """Parse <keys> = <output> format"""
        try:
            keys_part, output_part = line.split("=", 1)
            keys = [k.strip().lower() for k in keys_part.replace("+", " ").split()]
            output = output_part.strip()
            if keys and output:
                self.add_rule(keys, output, default_timeout, default_char_delay, default_word_delay)
        except Exception as e:
            print(f"Error parsing equals format: {line} - {e}")

    def _parse_colon_format(self, line, default_timeout, default_char_delay, default_word_delay):
        """Parse <keys>: <output> format"""
        try:
            keys_part, output_part = line.split(":", 1)
            keys = [k.strip().lower() for k in keys_part.replace("+", " ").split()]
            output = output_part.strip()
            if keys and output:
                self.add_rule(keys, output, default_timeout, default_char_delay, default_word_delay)
        except Exception as e:
            print(f"Error parsing colon format: {line} - {e}")

    # Keep the original method for backward compatibility
    def add_rules_from_if_logic(self, logic_text, default_timeout=1.0, default_char_delay=0.02, default_word_delay=0.15):
        return self.add_rules_from_logic(logic_text, default_timeout, default_char_delay, default_word_delay)

    # -------------------------
    # Keyboard listener
    # -------------------------
    def _keyboard_listener(self):
        keyboard.hook(self._on_key_event)
        keyboard.wait()

    def _on_key_event(self, event):
        if event.event_type != "down":
            return
        if self.is_typing:
            return

        key = event.name.lower()
        now = time.time()

        with self.lock:
            self.buffer.append(key)
            self.buffer_time.append(now)

            # Cancel previous lookahead timer
            if self.lookahead_timer and self.lookahead_timer.is_alive():
                self.lookahead_timer.cancel()

            # Start a new lookahead timer (short delay to check for longer sequences)
            self.lookahead_timer = threading.Timer(0.05, self._process_buffer)
            self.lookahead_timer.start()

    # -------------------------
    # Enhanced buffer processing with longest-match
    # -------------------------
    def _process_buffer(self):
        with self.lock:
            if not self.buffer:
                return

            # Clean up expired buffer entries
            current_time = time.time()
            max_timeout = 1.0
            if self.rules:
                max_timeout = max(r["timeout"] for r in self.rules)
            
            valid_indices = []
            for i, t in enumerate(self.buffer_time):
                if current_time - t <= max_timeout:
                    valid_indices.append(i)

            if not valid_indices:
                self.buffer.clear()
                self.buffer_time.clear()
                return
                
            # Keep only valid entries
            self.buffer = [self.buffer[i] for i in valid_indices]
            self.buffer_time = [self.buffer_time[i] for i in valid_indices]

            while self.buffer:
                longest_rule = None
                max_len = 0

                # Check all rules for possible match
                for rule in self.rules:
                    rule_len = len(rule["keys"])
                    if rule_len > len(self.buffer) or rule_len <= max_len:
                        continue
                    
                    # Check if buffer ends with this rule's keys
                    if self.buffer[-rule_len:] == rule["keys"]:
                        # Check timeout for sequence
                        seq_start_time = self.buffer_time[-rule_len]
                        seq_end_time = self.buffer_time[-1]
                        if seq_end_time - seq_start_time <= rule["timeout"]:
                            longest_rule = rule
                            max_len = rule_len

                if longest_rule:
                    # Calculate remaining wait time
                    seq_start_time = self.buffer_time[-max_len]
                    remaining_wait = max(0, longest_rule["timeout"] - (time.time() - seq_start_time))
                    
                    # Start delayed typing
                    timer = threading.Timer(remaining_wait, self._type_output, args=[longest_rule, max_len])
                    timer.start()
                    self.active_timers.append(timer)

                    # Remove used keys from buffer
                    del self.buffer[-max_len:]
                    del self.buffer_time[-max_len:]
                    break
                else:
                    # No match found, keep buffer for future keys
                    break

    # -------------------------
    # Type output safely
    # -------------------------
    def _type_output(self, rule, keys_used_count):
        self.is_typing = True
        try:
            # Small delay to ensure previous keys are processed
            time.sleep(0.01)
            
            output = rule["output"]
            char_delay = rule["char_delay"]
            word_delay = rule["word_delay"]
            
            # Type the output with specified delays
            for i, char in enumerate(output):
                pyautogui.write(char)
                if i < len(output) - 1:
                    # If next character is space, use word delay, else char delay
                    if output[i+1] == ' ':
                        time.sleep(word_delay)
                    else:
                        time.sleep(char_delay)
                        
        except Exception as e:
            print(f"Error typing output: {e}")
        finally:
            self.is_typing = False

    # -------------------------
    # Utilities
    # -------------------------
    def clear_rules(self):
        with self.lock:
            # Cancel all active timers
            for timer in self.active_timers:
                if timer and timer.is_alive():
                    timer.cancel()
            self.active_timers.clear()
            
            self.rules.clear()
            self.buffer.clear()
            self.buffer_time.clear()

    def debug_rules(self):
        return [{
            "keys": r["keys"],
            "output": r["output"],
            "timeout": r["timeout"],
            "char_delay": r["char_delay"],
            "word_delay": r["word_delay"]
        } for r in self.rules]

    def get_rules_count(self):
        return len(self.rules)