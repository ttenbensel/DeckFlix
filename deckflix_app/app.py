#!/usr/bin/env python3

from pathlib import Path
import shutil

from deckflix_app.scanner import scan_videos, count_videos
from deckflix_app.health import library_report, quality_score, size_gb

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
    report = library_report(MOVIES, TV)

    print()
    print("Library Health")
    print("──────────────")
    print(f"Movies video files:      {len(report['movies'])}")
    print(f"TV video files:          {len(report['tv'])}")
    print(f"Possible duplicates:     {len(report['duplicates'])}")
    print(f"Sample/junk candidates:  {len(report['junk'])}")
    print(f"Nested movie warnings:   {len(report['nested'])}")
    print()
    print("Nothing has been changed.")


def repair_preview():
    report = library_report(MOVIES, TV)

    while True:
        print()
        print("Repair Preview")
        print("──────────────")
        print("Dry-run only. Nothing will be moved, renamed, or deleted.")
        print()
        print(f"1. Review sample/junk files       {len(report['junk'])}")
        print(f"2. Review nested movie warnings   {len(report['nested'])}")
        print(f"3. Review duplicate groups        {len(report['duplicates'])}")
        print("4. Quarantine information")
        print("5. Back")
        print()

        choice = input("Select repair option: ").strip()

        if choice == "1":
            print()
            print("Sample/Junk Files")
            print("─────────────────")
            if report["junk"]:
                for f in report["junk"]:
                    print(f"[WOULD QUARANTINE] {f}")
            else:
                print("None found")
            input("\nPress Enter to continue...")

        elif choice == "2":
            print()
            print("Nested Movie Warnings")
            print("─────────────────────")
            if report["nested"]:
                for f in report["nested"][:50]:
                    print(f"[WOULD REVIEW MOVE] {f}")
                if len(report["nested"]) > 50:
                    print(f"...and {len(report['nested']) - 50} more")
            else:
                print("None found")
            input("\nPress Enter to continue...")

        elif choice == "3":
            print()
            print("Duplicate Review")
            print("────────────────")
            shown = 0
            for title, files in sorted(report["duplicates"].items()):
                ranked = sorted(files, key=quality_score, reverse=True)
                keep = ranked[0]

                print()
                print(title.title())
                print(f"[KEEP]   score {quality_score(keep):>3} {size_gb(keep):>5.1f} GB {keep}")

                for f in ranked[1:]:
                    print(f"[REVIEW] score {quality_score(f):>3} {size_gb(f):>5.1f} GB {f}")

                shown += 1
                if shown >= 20:
                    break

            input("\nPress Enter to continue...")

        elif choice == "4":
            print()
            print("Quarantine")
            print("──────────")
            print("Future repair actions will move files here first:")
            print("/mnt/dest4tb/deckflix-quarantine")
            print()
            print("DeckFlix rule:")
            print("Never delete first. Quarantine, verify, then remove later.")
            input("\nPress Enter to continue...")

        elif choice == "5":
            break

        else:
            print("Invalid option.")


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
