# core/macro_engine.py
import time
import threading
import pyautogui   # type: ignore
import keyboard    # type: ignore
import subprocess
import webbrowser
from typing import Callable, Dict, Any, Optional, List

"""
MacroEngine supports:
- single/combo hotkeys (trigger string like 'a' or 'ctrl+shift+a')
- two-key SEQUENCE macros (first_key -> second_key within a time window)
- per-macro delay_before (seconds) and char_delay (pyautogui interval)
"""

class MacroEngine:
    def __init__(self):
        # store macros by id -> macro dict
        # macro dict fields: {
        #   "id": str,
        #   "trigger": str,           # hotkey string for single/combo (e.g., 'a' or 'ctrl+alt+x')
        #   "type": "single"|"combo"|"sequence",
        #   "value": str,             # text/path/command/URL or description
        #   "action": Callable,       # callable to execute (already bound to value via closure)
        #   "delay_before": float,    # seconds before running action
        #   "char_delay": float,      # seconds between characters for typing
        #   "sequence": List[str] or None,  # for sequence: ['i','b']
        #   "window": float,          # sequence window seconds
        #   "hotkey_registered": bool,
        #   "sequence_registered": bool
        # }
        self.macros: Dict[str, Dict[str, Any]] = {}

        # pending store for sequences: first_key -> (expire_time, macro_id)
        self._pending_first: Dict[str, (float, str)] = {}

        # Lock to protect shared structures when registering/removing macros
        self._lock = threading.Lock()

    # helper to run action respecting delays and char_delay
    def _run_action(self, macro: Dict[str, Any]):
        """Run macro action in separate thread so keyboard events are not blocked."""
        def _worker():
            try:
                delay_before = float(macro.get("delay_before") or 0)
            except Exception:
                delay_before = 0
            if delay_before > 0:
                time.sleep(delay_before)

            # If this macro types text and char_delay > 0, use pyautogui.write with interval
            char_delay = float(macro.get("char_delay") or 0)
            # macro['action'] should be a callable that optionally accepts 'char_delay' or already bound
            try:
                # If action expects char_delay param, pass it; otherwise call directly
                # We'll attempt direct call first.
                macro["action"]()
            except TypeError:
                # fallback: try passing char_delay
                macro["action"](char_delay)
            except Exception:
                # best-effort: try calling anyway
                try:
                    macro["action"]()
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def _make_typing_action(self, text: str, char_delay: float):
        """Return action callable for typing text. Uses pyautogui.write with interval."""
        def action():
            # pyautogui.write supports interval param; if char_delay==0 this is fine.
            pyautogui.write(text, interval=char_delay)
        return action

    def _make_open_app_action(self, path: str):
        def action():
            try:
                subprocess.Popen(path)
            except Exception:
                # try as command
                subprocess.run(path, shell=True)
        return action

    def _make_run_command_action(self, cmd: str):
        def action():
            subprocess.run(cmd, shell=True)
        return action

    def _make_open_website_action(self, url: str):
        def action():
            try:
                webbrowser.open(url)
            except Exception:
                # ignore
                pass
        return action

    def add_macro(self,
                  macro_id: str,
                  trigger: Optional[str],
                  mtype: str,
                  value: str,
                  delay_before: float = 0.0,
                  char_delay: float = 0.0,
                  sequence: Optional[List[str]] = None,
                  window: float = 1.0):
        """
        Add macro.

        macro_id: unique id (string)
        trigger: hotkey trigger string for single/combo (e.g. 'a' or 'ctrl+shift+a'). For sequence type, this can be first key or None.
        mtype: 'single' | 'combo' | 'sequence'
        value: the action value (text, path, command, URL)
        delay_before: seconds before execution
        char_delay: for typing interval
        sequence: for sequence type, list of two keys ['first','second']
        window: time window in seconds for sequence second key
        """

        with self._lock:
            # if macro_id exists, remove first
            if macro_id in self.macros:
                self.remove_macro(macro_id)

            macro: Dict[str, Any] = {
                "id": macro_id,
                "trigger": trigger,
                "type": mtype,
                "value": value,
                "delay_before": float(delay_before or 0),
                "char_delay": float(char_delay or 0),
                "sequence": sequence,
                "window": float(window or 1.0),
                "hotkey_registered": False,
                "sequence_registered": False
            }

            # Build action callable based on mtype/value
            if mtype in ("single", "combo", "sequence"):
                # choose action factory by content look (we assume value string tells purpose)
                # but UI will pass the right factory choice; here we'll decide:
                # if value looks like a path and mtype not 'Type Text' the caller should have bound action.
                # For safety, if value contains 'http' or 'www', use open_website
                if value.startswith("http://") or value.startswith("https://") or value.startswith("www."):
                    action = self._make_open_website_action(value)
                else:
                    # Default assume "Type Text"
                    action = self._make_typing_action(value, macro["char_delay"])
            else:
                action = self._make_typing_action(value, macro["char_delay"])

            macro["action"] = action

            # Register hotkeys for single/combo
            if mtype in ("single", "combo"):
                # register hotkey with suppress=True to avoid original key typing
                if trigger:
                    keyboard.add_hotkey(trigger, lambda m=macro: self._run_action(m), suppress=True)
                    macro["hotkey_registered"] = True

            # Register sequence handling (supports only 2-key sequences)
            if mtype == "sequence" and sequence and len(sequence) == 2:
                first_key = sequence[0]
                second_key = sequence[1]

                # handler for first key: set pending with expiry
                def first_handler(fk=first_key, mid=macro_id, wnd=macro["window"]):
                    expire = time.time() + float(wnd)
                    with self._lock:
                        self._pending_first[fk] = (expire, mid)
                # register first key (suppress original to avoid typing)
                keyboard.add_hotkey(first_key, first_handler, suppress=True)

                # handler for second key: check pending first and run sequence action if valid
                def second_handler(sk=second_key):
                    with self._lock:
                        # find any pending first key that matches sk's expected predecessor
                        # simple check: look for any entry where pending key maps to macro_id whose sequence second matches sk
                        now = time.time()
                        to_run_mid = None
                        to_delete = []
                        for fk, (expire, mid) in list(self._pending_first.items()):
                            if expire >= now and mid in self.macros:
                                mac = self.macros[mid]
                                seq = mac.get("sequence") or []
                                if len(seq) == 2 and seq[1] == sk:
                                    to_run_mid = mid
                                    to_delete.append(fk)
                                    break
                                else:
                                    # if expired or not matching, clear later
                                    if expire < now:
                                        to_delete.append(fk)
                        # clean up expired/popped entries
                        for fk in to_delete:
                            if fk in self._pending_first:
                                del self._pending_first[fk]
                        if to_run_mid:
                            macro_to_run = self.macros.get(to_run_mid)
                            if macro_to_run:
                                # execute sequence macro
                                self._run_action(macro_to_run)

                # register the second key handler (suppress True so the second key doesn't type)
                keyboard.add_hotkey(second_key, second_handler, suppress=True)

                macro["sequence_registered"] = True

            # save macro
            self.macros[macro_id] = macro

    def remove_macro(self, macro_id: str):
        """Remove macro by id. Unregister hotkeys if needed."""
        with self._lock:
            macro = self.macros.get(macro_id)
            if not macro:
                return
            # unregister hotkey(s)
            try:
                trig = macro.get("trigger")
                if macro.get("hotkey_registered") and trig:
                    keyboard.remove_hotkey(trig)
            except Exception:
                pass
            # For sequences, unregister both keys (best-effort)
            try:
                if macro.get("sequence_registered") and macro.get("sequence"):
                    seq = macro.get("sequence")
                    if seq and len(seq) == 2:
                        keyboard.remove_hotkey(seq[0])
                        keyboard.remove_hotkey(seq[1])
            except Exception:
                pass

            # clean any pending entries referencing this macro
            for fk, (expire, mid) in list(self._pending_first.items()):
                if mid == macro_id:
                    del self._pending_first[fk]

            # finally remove
            del self.macros[macro_id]

    def list_macros(self) -> Dict[str, Dict[str, Any]]:
        """Return a shallow copy of macro definitions for UI display."""
        with self._lock:
            return {mid: {
                "id": mid,
                "trigger": m.get("trigger"),
                "type": m.get("type"),
                "value": m.get("value"),
                "delay_before": m.get("delay_before"),
                "char_delay": m.get("char_delay"),
                "sequence": m.get("sequence"),
                "window": m.get("window")
            } for mid, m in self.macros.items()}
