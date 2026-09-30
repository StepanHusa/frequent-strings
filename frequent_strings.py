#!/usr/bin/env python3
"""frequent_strings — pick a saved string and inject it at the cursor."""

import argparse
import json
import os
import subprocess
import sys

DATA_PATH = os.path.expanduser("~/.local/share/frequent_strings/strings.json")


# ── Storage ───────────────────────────────────────────────────────────────────

def load_strings() -> list[dict]:
    try:
        with open(DATA_PATH) as f:
            data = json.load(f)
        return sorted(data, key=lambda x: x.get("count", 0), reverse=True)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Corrupted data file {DATA_PATH}: {e}") from e


def save_strings(strings: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(strings, f, indent=2, ensure_ascii=False)


def add_string(strings: list[dict], text: str) -> tuple[list[dict], bool]:
    """Return (updated_list, was_added). Does not save to disk."""
    text = text.strip()
    if not text:
        return strings, False
    if any(s["text"] == text for s in strings):
        return strings, False
    strings.append({"text": text, "count": 0})
    return strings, True


def increment_count(strings: list[dict], text: str) -> list[dict]:
    for item in strings:
        if item["text"] == text:
            item["count"] = item.get("count", 0) + 1
            return strings
    strings.append({"text": text, "count": 1})
    return strings


# ── System interaction ────────────────────────────────────────────────────────

def inject_text(text: str) -> None:
    try:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "0", "--", text],
            timeout=30,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"xdotool injection failed: {e}") from e
    except FileNotFoundError:
        raise RuntimeError("xdotool not found — install it with: sudo apt install xdotool")


def inject_text_via_clipboard(text: str) -> None:
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            timeout=5,
            check=True,
        )
        subprocess.run(["xdotool", "key", "ctrl+v"], timeout=5, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Clipboard injection failed: {e}") from e
    except FileNotFoundError:
        raise RuntimeError("xclip not found — install it with: sudo apt install xclip")


def get_clipboard() -> tuple[str | None, str | None]:
    """Return (text, None) on success or (None, reason) on failure."""
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        text = result.stdout.strip()
        if not text:
            return None, "Clipboard is empty."
        return text, None
    except subprocess.CalledProcessError:
        return None, "Could not read clipboard."
    except FileNotFoundError:
        return None, "xclip not found — install it with: sudo apt install xclip"


# ── App window ────────────────────────────────────────────────────────────────

class FrequentStringsApp:
    WIDTH = 560
    HEIGHT = 420

    HINT_DEFAULT = "Enter=insert  Ctrl+N=add clipboard  Del=delete  Esc=close"

    def __init__(self, original_wid: str):
        self._original_wid = original_wid
        self._strings = load_strings()
        self._filtered: list[dict] = list(self._strings)

        import tkinter as tk
        self._tk = tk
        self._root = tk.Tk()
        self._root.title("frequent_strings")
        self._root.resizable(True, True)
        self._root.attributes("-topmost", True)
        self._center()

        # Search bar
        search_frame = tk.Frame(self._root, padx=8, pady=6)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="Search:").pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        self._search_entry = tk.Entry(search_frame, textvariable=self._search_var)
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Listbox
        list_frame = tk.Frame(self._root, padx=8)
        list_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self._listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode="single",
            activestyle="dotbox",
            font=("TkFixedFont", 10),
        )
        scrollbar.config(command=self._listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self._listbox.pack(side="left", fill="both", expand=True)

        # Hint bar
        self._hint = tk.Label(
            self._root,
            text=self.HINT_DEFAULT,
            fg="#888888",
            font=("TkDefaultFont", 9),
            pady=5,
        )
        self._hint.pack(side="bottom")

        self._populate_list()

        # Search entry bindings
        self._search_entry.bind("<Down>", self._focus_list)
        self._search_entry.bind("<Return>", lambda e: self._do_insert())
        self._search_entry.bind("<Escape>", lambda e: self._root.destroy())

        # Listbox bindings
        self._listbox.bind("<Return>", lambda e: self._do_insert())
        self._listbox.bind("<Double-Button-1>", lambda e: self._do_insert())
        self._listbox.bind("<Delete>", lambda e: self._do_delete())
        self._listbox.bind("<Escape>", lambda e: self._root.destroy())

        # Global bindings
        self._root.bind("<Escape>", lambda e: self._root.destroy())
        self._root.bind("<Control-n>", lambda e: self._add_from_clipboard())

        self._search_entry.focus_set()

    def _center(self):
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x = (sw - self.WIDTH) // 2
        y = (sh - self.HEIGHT) // 2
        self._root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _populate_list(self):
        self._listbox.delete(0, "end")
        for item in self._filtered:
            count = item.get("count", 0)
            preview = item["text"].replace("\n", "\\n")[:80]
            self._listbox.insert("end", f"[{count:5d}]  {preview}")
        if self._filtered:
            self._listbox.selection_set(0)
            self._listbox.activate(0)

    def _on_search(self, *_):
        query = self._search_var.get().lower()
        self._filtered = (
            [s for s in self._strings if query in s["text"].lower()]
            if query
            else list(self._strings)
        )
        self._populate_list()

    def _focus_list(self, event=None):
        self._listbox.focus_set()
        return "break"

    def _selected_item(self) -> dict | None:
        sel = self._listbox.curselection()
        if sel:
            return self._filtered[sel[0]]
        idx = self._listbox.index("active")
        if self._filtered and 0 <= idx < len(self._filtered):
            return self._filtered[idx]
        return None

    def _do_insert(self):
        item = self._selected_item()
        if not item:
            return
        text = item["text"]
        increment_count(self._strings, text)
        save_strings(self._strings)
        self._root.destroy()
        if self._original_wid:
            try:
                subprocess.run(
                    ["xdotool", "windowfocus", "--sync", self._original_wid],
                    timeout=3,
                    capture_output=True,
                )
            except Exception:
                pass
        try:
            inject_text(text)
        except RuntimeError:
            inject_text_via_clipboard(text)

    def _do_delete(self):
        item = self._selected_item()
        if not item:
            return
        text = item["text"]
        self._strings = [s for s in self._strings if s["text"] != text]
        self._filtered = [s for s in self._filtered if s["text"] != text]
        save_strings(self._strings)
        self._populate_list()

    def _add_from_clipboard(self):
        text, err = get_clipboard()
        if err:
            self._show_hint(err, temporary=True)
            return
        self._strings, added = add_string(self._strings, text)
        if not added:
            self._show_hint(f"Already in list: {text[:40]!r}", temporary=True)
            return
        save_strings(self._strings)
        query = self._search_var.get().lower()
        self._filtered = (
            [s for s in self._strings if query in s["text"].lower()]
            if query
            else list(self._strings)
        )
        self._populate_list()
        try:
            idx = next(i for i, s in enumerate(self._filtered) if s["text"] == text)
            self._listbox.selection_clear(0, "end")
            self._listbox.selection_set(idx)
            self._listbox.activate(idx)
            self._listbox.see(idx)
        except StopIteration:
            pass
        self._show_hint(f"Added: {text[:50]!r}", temporary=True)

    def _show_hint(self, msg: str, temporary: bool = False):
        self._hint.config(text=msg)
        if temporary:
            self._root.after(2500, lambda: self._hint.config(text=self.HINT_DEFAULT))

    def run(self):
        self._root.mainloop()


# ── CLI commands ──────────────────────────────────────────────────────────────

def cmd_app(_args=None):
    original_wid = subprocess.run(
        ["xdotool", "getactivewindow"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    app = FrequentStringsApp(original_wid)
    app.run()


def cmd_add(args):
    text = args.text.strip()
    if not text:
        print("error: text is empty", file=sys.stderr)
        sys.exit(1)
    strings = load_strings()
    strings, added = add_string(strings, text)
    if added:
        save_strings(strings)
        print(f"Added: {text!r}")
    else:
        print(f"Already exists: {text!r}")


def cmd_list(_args=None):
    strings = load_strings()
    if not strings:
        print("(no strings saved yet)")
        return
    for item in strings:
        print(f"{item.get('count', 0):5d}  {item['text']}")


def main():
    parser = argparse.ArgumentParser(
        prog="frequent_strings",
        description="Pick a saved string and inject it at the cursor.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("app", help="Open the picker window").set_defaults(func=cmd_app)

    p_add = sub.add_parser("add", help="Add a string from the command line")
    p_add.add_argument("text", help="The string to add")
    p_add.set_defaults(func=cmd_add)

    sub.add_parser("list", help="Print all saved strings with counts").set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
