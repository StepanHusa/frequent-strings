#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

for cmd in python3 xdotool xclip; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "error: $cmd not found"
        echo "  sudo apt install xdotool xclip"
        exit 1
    fi
done

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "error: tkinter not available"
    echo "  sudo apt install python3-tk"
    exit 1
fi

mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.local/share/frequent_strings"

cat > "$BIN_DIR/frequent_strings" <<EOF
#!/usr/bin/env bash
exec python3 "$SCRIPT_DIR/frequent_strings.py" "\$@"
EOF
chmod +x "$BIN_DIR/frequent_strings"

echo "Installed: $BIN_DIR/frequent_strings"
echo ""
echo "Make sure ~/.local/bin is in your PATH:"
echo "  export PATH=\"\${HOME}/.local/bin:\${PATH}\""
echo ""
echo "Recommended hotkey binding (XFCE: Settings → Keyboard → Application Shortcuts):"
echo "  frequent_strings app   →  e.g. Super+S"
