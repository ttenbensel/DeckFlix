#!/usr/bin/env bash
set -e

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/deckflix"

echo "Installing DeckFlix from GitHub repo..."
echo "Source:  $SOURCE_DIR"
echo "Target:  $INSTALL_DIR"

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cp -R "$SOURCE_DIR/"* "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/deckflix.py"

mkdir -p /mnt/dest4tb/deckflix-logs
mkdir -p /mnt/dest4tb/deckflix-quarantine

echo
echo "DeckFlix installed."
echo
echo "Run with:"
echo "cd /opt/deckflix"
echo "./deckflix.py"
