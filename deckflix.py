#!/usr/bin/env python3

import sys

from deckflix_app.app import main
from deckflix_app.diagnostics import run_doctor


def command_line():
    if len(sys.argv) == 1:
        main()
        return 0

    command = sys.argv[1].strip().lower()

    if command == "doctor":
        return 0 if run_doctor() else 1

    print(f"Unknown command: {command}")
    print()
    print("Usage:")
    print("  ./deckflix.py")
    print("  ./deckflix.py doctor")
    return 2


if __name__ == "__main__":
    raise SystemExit(command_line())
