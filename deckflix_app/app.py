from pathlib import Path

from deckflix_app.dashboard import show_dashboard
from deckflix_app.health import library_report, quality_score, size_gb
from deckflix_app.import_queue import build_import_queue
from deckflix_app.queue_screen import show_queue
from deckflix_app.scanner import scan_videos
from deckflix_app.shuttle import scan_shuttle as shuttle_scan, compare_to_library
from deckflix_app.import_runner import run_import
from deckflix_app.version import APP_NAME, VERSION, CODENAME


MOVIES = Path("/mnt/dest4tb/movie")
TV = Path("/mnt/dest4tb/tv")
SHUTTLE = Path("/mnt/source2tb")


def logo():
    print("═══════════════════════════════════════════════")
    print(f"                 ⚓ {APP_NAME.upper()} ⚓")
    print("        Shipboard Media Management")
    print("═══════════════════════════════════════════════")
    print(f"Version {VERSION}")
    print(f"Codename: {CODENAME}")
    print()


def build_current_queue():
    shuttle = shuttle_scan(SHUTTLE)
    library_movies = scan_videos(MOVIES)
    comparison = compare_to_library(shuttle["media"], library_movies)
    return build_import_queue(comparison, library_movies)


def print_movie_item(item, prefix):
    if item.year:
        print(f"{prefix} 🎬 {item.title} ({item.year})")
    else:
        print(f"{prefix} 🎬 {item.title}")


def print_tv_item(item, prefix):
    print(f"{prefix} 📺 {item.title} S{item.season:02d}E{item.episode:02d}")


def print_media_item(item, prefix):
    if item.media_type == "tv":
        print_tv_item(item, prefix)
    else:
        print_movie_item(item, prefix)


def receive_shuttle():
    shuttle = shuttle_scan(SHUTTLE)
    library_movies = scan_videos(MOVIES)
    comparison = compare_to_library(shuttle["media"], library_movies)
    storage = shuttle["storage"]

    print()
    print("Receive Shuttle")
    print("═══════════════")
    print("Dry-run only. Nothing will be copied, moved, or deleted.")
    print()

    print("Drive")
    print("─────")
    if shuttle["connected"]:
        print("Status              Connected")
    else:
        print("Status              Not Found")

    print(f"Path                {shuttle['path']}")

    if storage["available"]:
        print(f"Capacity            {storage['total_tb']:.2f} TB")
        print(f"Used                {storage['used_tb']:.2f} TB")
        print(f"Free                {storage['free_tb']:.2f} TB")

    print()
    print("Media Summary")
    print("─────────────")
    print(f"Video files          {len(shuttle['files'])}")
    print(f"Movies found         {len(shuttle['movies'])}")
    print(f"TV episodes found    {len(shuttle['tv'])}")
    print()
    print(f"New items            {len(comparison['new_media'])}")
    print(f"Possible duplicates  {len(comparison['duplicates'])}")

    print()
    print("Import Preview")
    print("──────────────")

    if not shuttle["files"]:
        print("No shuttle media found.")
    else:
        if comparison["new_media"]:
            print("New media")
            print("─────────")
            for item in comparison["new_media"][:20]:
                print_media_item(item, "[NEW]")

        if comparison["duplicates"]:
            print()
            print("Needs review")
            print("────────────")
            for item in comparison["duplicates"][:20]:
                print_media_item(item, "[DUPLICATE]")

    print()
    print("Nothing has been changed.")


def import_queue():
    queue = build_current_queue()
    show_queue(queue)

    while True:
        print()
        print("Queue Options")
        print("─────────────")
        print("1. Run approved imports")
        print("2. Return to main menu")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            success = run_import(
                queue,
                MOVIES,
                TV,
            )

            if success:
                input("\nPress Enter after verifying the copy...")

            break

        elif choice == "2":
            break

        else:
            print("Invalid option.")


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
        print("3. Import Queue")
        print("4. Library Health")
        print("5. Repair Preview")
        print("6. Ship Mode")
        print("7. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            show_dashboard(MOVIES, TV, SHUTTLE)
        elif choice == "2":
            receive_shuttle()
        elif choice == "3":
            import_queue()
        elif choice == "4":
            library_health()
        elif choice == "5":
            repair_preview()
        elif choice == "6":
            ship_mode()
        elif choice == "7":
            print("Securing DeckFlix console.")
            break
        else:
            print("Invalid option.")

        input("\nPress Enter to return to menu...")
