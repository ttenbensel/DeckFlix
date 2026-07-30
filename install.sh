#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${DECKFLIX_INSTALL_DIR:-/opt/deckflix}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "Installing DeckFlix into: $INSTALL_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python 3 is required."
    exit 1
fi

if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
    echo "ERROR: Python venv support is missing."
    echo "On Debian, install it with:"
    echo "  sudo apt install python3-venv"
    exit 1
fi

cd "$INSTALL_DIR"

if [ ! -f pyproject.toml ]; then
    echo "ERROR: pyproject.toml was not found in $INSTALL_DIR"
    exit 1
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install .

sudo ln -sf \
    "$INSTALL_DIR/.venv/bin/deckflix" \
    /usr/local/bin/deckflix

echo
echo "DeckFlix installed successfully."
echo "Run:"
echo "  deckflix status"
