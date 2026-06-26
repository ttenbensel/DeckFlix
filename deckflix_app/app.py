from pathlib import Path

from deckflix_app.dashboard import show_dashboard
from deckflix_app.health import library_report, quality_score, size_gb
from deckflix_app.scanner import scan_videos
from deckflix_app.shuttle import scan_shuttle as shuttle_scan, compare_to_library

VERSION = "0.4.4"

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


def receive_shuttle():
    shuttle = shuttle_scan(SHUTTLE)
    library_movies = scan_videos(MOVIES)
    comparison = compare_to_library(shuttle["media"], library_movies)
    storage = shuttle["storage"]

    print()
    print("Receive Shuttle")
    print("───────────────")
    print("Dry-run only. Nothing will be copied, moved, or deleted.")
    print()

    if shuttle["connected"]:
        print("Status              Shuttle Connected")
    else:
        print("Status              Shuttle Not Found")

    print(f"Shuttle Path        {shuttle['path']}")

    if storage["available"]:
        print(f"Storage Used        {storage['used_tb']:.2f} TB / {storage['total_tb']:.2f} TB")
        print(f"Free Space          {storage['free_tb']:.2f} TB")

    print()
    print(f"Video files          {len(shuttle['files'])}")
    print(f"Movie files          {len(shuttle['movies'])}")
    print(f"TV episode files     {len(shuttle['tv'])}")
    print()
    print(f"New media            {len(comparison['new_media'])}")
    print(f"Possible duplicates  {len(comparison['duplicates'])}")
    print()

    print("Import Plan")
    print("───────────")

    if not shuttle["files"]:
        print("No shuttle media found.")

    for item in comparison["new_media"][:30]:
        print(f"[NEW] {item.path}")

    for item in comparison["duplicates"][:30]:
        print(f"[REVIEW DUPLICATE] {item.path}")

    if comparison["new_media"]:
        print()
        print("First New Items")
        print("───────────────")

        for item in comparison["new_media"][:10]:
            if item.media_type == "movie":
                if item.year:
                    print(f"🎬 {item.title} ({item.year})")
                else:
                    print(f"🎬 {item.title}")
            else:
                print(f"📺 {item.title} S{item.season:02d}E{item.episode:02d}")

    print()
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
                for file in report["junk"]:
                    print(f"[WOULD QUARANTINE] {file}")
            else:
                print("None found")
            input("\nPress Enter to continue...")

        elif choice == "2":
            print()
            print("Nested Movie Warnings")
            print("─────────────────────")
            if report["nested"]:
                for file in report["nested"][:50]:
                    print(f"[WOULD REVIEW MOVE] {file}")
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

                for file in ranked[1:]:
                    print(f"[REVIEW] score {quality_score(file):>3} {size_gb(file):>5.1f} GB {file}")

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
    print("Internet Tasks    Allowed")
    print("Background Work   Normal")
    print()
    print("Sea Mode controls coming next.")


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
            show_dashboard(MOVIES, TV, SHUTTLE)
        elif choice == "2":
            receive_shuttle()
        elif choice == "3":
            library_health()
        elif choice == "4":
            repair_preview()
        elif choice == "5":
            ship_mode()
        elif choice == "6":
            print("Securing DeckFlix console.")
            break
        else:
            print("Invalid option.")

        input("\nPress Enter to return to menu...")
