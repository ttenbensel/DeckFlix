from pathlib import Path

from deckflix_app.dashboard import show_dashboard
from deckflix_app.health import library_report, quality_score, size_gb
from deckflix_app.import_queue import build_import_queue
from deckflix_app.queue_screen import show_queue
from deckflix_app.scanner import scan_videos
from deckflix_app.shuttle import scan_shuttle as shuttle_scan, compare_to_library
from deckflix_app.import_runner import run_import
from deckflix_app.version import APP_NAME, VERSION, CODENAME
from deckflix_app.library_health import show_library_health
from deckflix_app.duplicate_inspector import show_duplicate_inspector
from deckflix_app.repair_queue_screen import show_repair_queue
from deckflix_app.services.release_inspector import (
    build_release_report,
    show_release_report,
)
from deckflix_app.services.media_index import MediaIndex
from deckflix_app.services.file_compare import (
    compare_release_files,
    show_file_comparison,
)
from deckflix_app.services.cleanup_planner import (
    build_cleanup_plan,
    show_cleanup_plan,
)
from deckflix_app.services.repair_queue import RepairQueue

from deckflix_app.services.repair_executor import (
    build_execution_preview,
    show_execution_preview,
    confirm_execution,
    execute_preview,
    show_execution_result,
)

MOVIES = Path("/mnt/library1/movie")
TV = Path("/mnt/library1/tv")
SHUTTLE = Path("/mnt/source2tb")
QUARANTINE_ROOT = Path("/mnt/library1/deckflix-quarantine")
ENABLE_REAL_REPAIRS = False
SESSION_MEDIA_INDEX = None
SESSION_REPAIR_QUEUE = RepairQueue()

def get_session_media_index(refresh=False):
    """
    Return the session-wide MediaIndex.

    The library is scanned only on first use or when refresh=True.
    """

    global SESSION_MEDIA_INDEX

    if SESSION_MEDIA_INDEX is None or refresh:
        print()
        print("Scanning media libraries...")

        index = MediaIndex()
        index.rebuild()

        SESSION_MEDIA_INDEX = index

        print(
            f"Scan complete: "
            f"{index.movie_count} movies, "
            f"{index.tv_count} TV episodes"
        )

    return SESSION_MEDIA_INDEX

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
    show_library_health(
        MOVIES,
        TV,
    )

    input("\nPress Enter to return to the main menu...")


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
        print("5. Duplicate Inspector")
        print("6. Release Inspector")
        print("7. Repair Queue")
        print("8. Ship Mode")
        print("9. Exit")
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
            duplicate_inspector()

        elif choice == "6":
            release_inspector()

        elif choice == "7":
            session_repair_queue_screen()

        elif choice == "8":
            ship_mode()

        elif choice == "9":
            print("Securing DeckFlix console.")
            break

        else:
            print("Invalid option.")

        input("\nPress Enter to return to menu...")

def duplicate_inspector():
    show_duplicate_inspector(
        MOVIES,
        TV,
    )

    input("\nPress Enter to return to the main menu...")

def session_repair_queue_screen():
    """
    Display CleanupPlan objects stored in the session repair queue.

    Read-only. Nothing is moved, quarantined, or deleted.
    """

    plans = SESSION_REPAIR_QUEUE.plans()

    print()
    print("Repair Queue")
    print("════════════")

    if not plans:
        print()
        print("Repair queue is empty.")
        return

    print()
    print(f"Queued releases     {SESSION_REPAIR_QUEUE.count}")
    print(
        f"Recoverable space   "
        f"{SESSION_REPAIR_QUEUE.recoverable_bytes / 1024**3:.2f} GB"
    )

    for number, plan in enumerate(plans, start=1):
        title, year, _ = plan.release_key

        print()
        print(f"{number}. {title.title()} ({year or 'unknown'})")
        print(f"   Risk             {plan.risk}")
        print(f"   Quarantine       {len(plan.quarantine)} file(s)")
        print(f"   Recoverable      {plan.recovered_gb:.2f} GB")

        for item in plan.quarantine:
            print(f"   [PROPOSED]       {item.path}")

    print()
    print("Read-only queue. Nothing has been changed.")
    print()
    print("D. Dry-run queued repairs")
    print("E. Execute approved repairs")
    print("0. Back")
    print()

    choice = input("Select option: ").strip().lower()

    if choice == "d":
        preview = build_execution_preview(
            plans,
            QUARANTINE_ROOT,
        )

        show_execution_preview(preview)
        input("\nPress Enter...")

    elif choice == "e":
        preview = build_execution_preview(
            plans,
            QUARANTINE_ROOT,
        )

        show_execution_preview(preview)

        if not ENABLE_REAL_REPAIRS:
            print()
            print("Real repair execution is disabled.")
            print("DeckFlix is running in Safe Preview Mode.")
            input("\nPress Enter...")
            return

        if not confirm_execution(preview):
            print()
            print("Execution cancelled.")
            input("\nPress Enter...")
            return

        result = execute_preview(preview)
        show_execution_result(result)

        input("\nPress Enter...")

def release_actions(index, release):
    """
    Interactive actions for a single release.
    Read-only.
    """

    while True:
        print()
        print("Release Actions")
        print("═══════════════")

        title, year, _ = release.key

        print()
        print(f"{title.title()} ({year or 'unknown'})")
        print()

        print("1. View Report")
        print("2. Compare Files")
        print("3. Simulate Cleanup")
        print("4. Add to Repair Queue")
        print()
        print("0. Back")
        print()

        choice = input("Select option: ").strip()

        if choice == "0":
            return

        elif choice == "1":
            print()
            print("Checking fingerprints...")

            index.confirm_release_fingerprints([release])

            report = build_release_report(release)
            show_release_report(report)

            input("\nPress Enter...")

        elif choice == "2":
            print()
            print("Checking fingerprints...")

            index.confirm_release_fingerprints([release])

            result = compare_release_files(release)
            show_file_comparison(result)

            input("\nPress Enter...")

        elif choice == "3":
            print()
            print("Checking fingerprints...")

            index.confirm_release_fingerprints([release])

            plan = build_cleanup_plan(release)
            show_cleanup_plan(plan)

            input("\nPress Enter...")

        elif choice == "4":
            print()
            print("Checking fingerprints...")

            index.confirm_release_fingerprints([release])

            plan = build_cleanup_plan(release)

            if not plan.quarantine:
                print()
                print("No SHA-256-confirmed cleanup action available.")
                input("\nPress Enter...")
                continue

            SESSION_REPAIR_QUEUE.add(plan)

            print()
            print("Added to Repair Queue")
            print("─────────────────────")
            print(f"Risk              {plan.risk}")
            print(f"Files proposed    {len(plan.quarantine)}")
            print(f"Recoverable       {plan.recovered_gb:.2f} GB")
            print()
            print("Nothing has been moved.")

            input("\nPress Enter...")

def release_inspector():
    """
    Interactive Release Inspector.

    Uses the session-wide MediaIndex so repeated visits do not
    rescan the library. Read-only; nothing is modified.
    """

    index = get_session_media_index()
    releases = index.build_movie_releases()

    if not releases:
        print()
        print("No releases require inspection.")
        input("\nPress Enter...")
        return

    while True:
        print()
        print("Release Inspector")
        print("═════════════════")

        for number, release in enumerate(releases, start=1):
            title, year, _ = release.key

            status = "✓" if release.confirmed else "?"

            print(
                f"{number:2}. {status} "
                f"{title.title()} ({year or 'unknown'})"
            )

        print()
        print("R. Refresh library scan")
        print("0. Return")
        print()

        choice = input("Select release: ").strip().lower()

        if choice == "0":
            break

        if choice == "r":
            index = get_session_media_index(refresh=True)
            releases = index.build_movie_releases()
            continue

        if not choice.isdigit():
            print("Invalid option.")
            continue

        number = int(choice)

        if not 1 <= number <= len(releases):
            print("Invalid option.")
            continue

        release = releases[number - 1]

        release_actions(index, release)
