#!/usr/bin/env python3

from pathlib import Path

VERSION = "0.3.0"

MOVIES = Path("/mnt/dest4tb/movie")
TV = Path("/mnt/dest4tb/tv")
SHUTTLE = Path("/mnt/source2tb")


def logo():
    print(f"""
═══════════════════════════════════════════════
                 ⚓ DECKFLIX ⚓
        Shipboard Media Management
═══════════════════════════════════════════════
Version {VERSION}
""")


def count_videos(path):
    if not path.exists():
        return 0

    exts = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v"}

    return sum(
        1
        for f in path.rglob("*")
        if f.is_file() and f.suffix.lower() in exts
    )


def dashboard():
    movies = count_videos(MOVIES)
    tv = count_videos(TV)
    shuttle = count_videos(SHUTTLE)

    print()
    print("Bridge Dashboard")
    print("────────────────")
    print("Vessel Mode        ⚓ Harbour")
    print("Low Impact         Enabled")
    print()
    print(f"Movies             {movies}")
    print(f"TV Episodes        {tv}")
    print(f"Shuttle Videos     {shuttle}")
    print()
    print("Nothing has been changed.")


def scan_shuttle():
    print()
    print("Receive Shuttle")
    print("───────────────")
    print("Scanning shuttle drive...")
    print()
    print("Dry-run only.")
    print("Nothing has been changed.")


def library_health():
    print()
    print("Library Health")
    print("──────────────")
    print("Analysing library...")
    print()
    print("Nothing has been changed.")


def repair_preview():
    print()
    print("Repair Preview")
    print("──────────────")
    print("This feature is under construction.")
    print()
    print("Future versions will include:")
    print(" • Duplicate review")
    print(" • Better-quality detection")
    print(" • Sample file detection")
    print(" • Nested movie repair")
    print(" • Safe quarantine")
    print()
    print("Nothing has been changed.")


def ship_mode():
    print()
    print("Ship Mode")
    print("─────────")
    print("Current Mode      ⚓ Harbour")
    print("Low Impact        Enabled")
    print()
    print("Sea Mode coming soon.")


def main():
    while True:
        logo()

        print("1. Bridge Dashboard")
        print("2. Receive Shuttle")
        print("3. Library Health")
        print("4. Repair Preview")
        print("5. Ship Mode")
        print("6. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            dashboard()

        elif choice == "2":
            scan_shuttle()

        elif choice == "3":
            library_health()

        elif choice == "4":
            repair_preview()

        elif choice == "5":
            ship_mode()

        elif choice == "6":
            print("\nSecuring DeckFlix console.")
            break

        else:
             print("\nInvalid option.")

        input("\nPress Enter to return to menu...")
