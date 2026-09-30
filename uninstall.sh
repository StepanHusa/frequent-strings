#!/usr/bin/env bash
set -euo pipefail

rm -f "$HOME/.local/bin/frequent_strings"
echo "Removed: $HOME/.local/bin/frequent_strings"
echo ""
echo "Your saved strings are kept at: ~/.local/share/frequent_strings/strings.json"
echo "Remove manually if you want:  rm -rf ~/.local/share/frequent_strings"
