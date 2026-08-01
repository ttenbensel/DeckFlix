from pathlib import Path

from deckflix_app.scanner import scan_videos
from deckflix_app.shuttle import (
    compare_to_library,
    scan_shuttle,
)


def print_movie_item(item, prefix: str) -> None:
    if item.year:
        print(f"{prefix} 🎬 {item.title} ({item.year})")
    else:
        print(f"{prefix} 🎬 {item.title}")


def print_tv_item(item, prefix: str) -> None:
    print(
        f"{prefix} 📺 {item.title} "
        f"S{item.season:02d}E{item.episode:02d}"
    )


def print_media_item(item, prefix: str) -> None:
    if item.media_type == "tv":
        print_tv_item(item, prefix)
    else:
        print_movie_item(item, prefix)


def show_receive_shuttle(
    shuttle_path: Path,
    movie_library_path: Path,
) -> None:
    shuttle = scan_shuttle(shuttle_path)

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

    storage = shuttle["storage"]

    if storage["available"]:
        print(f"Capacity            {storage['total_tb']:.2f} TB")
        print(f"Used                {storage['used_tb']:.2f} TB")
        print(f"Free                {storage['free_tb']:.2f} TB")

    if not shuttle["connected"]:
        print()
        print("Shuttle scan cancelled.")
        print("Nothing has been changed.")
        return

    library_movies = scan_videos(movie_library_path)

    comparison = compare_to_library(
        shuttle["media"],
        library_movies,
    )

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
