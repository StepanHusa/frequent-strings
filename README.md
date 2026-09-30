# frequent_strings

A small Linux (X11) picker for strings you type often. Press a hotkey, pick a
saved string, and it is typed at the cursor in whatever window had focus.
Strings are sorted by how often you use them.

## Requirements

- Python 3 with tkinter (`sudo apt install python3-tk`)
- `xdotool` and `xclip` (`sudo apt install xdotool xclip`)
- An X11 session (typing is done via `xdotool`)

## Install

```bash
./install.sh
```

This creates the launcher `~/.local/bin/frequent_strings`. Bind a hotkey to
`frequent_strings app` (XFCE: Settings → Keyboard → Application Shortcuts).

## Usage

```bash
frequent_strings app          # open the picker window
frequent_strings add "text"   # add a string from the command line
frequent_strings list         # print all saved strings with counts
```

In the picker: type to filter, `Enter` inserts, `Ctrl+N` adds the clipboard
contents, `Del` deletes, `Esc` closes.

Strings are stored in `~/.local/share/frequent_strings/strings.json`.

## Uninstall

```bash
./uninstall.sh
```

Removes the launcher; your saved strings are kept.
