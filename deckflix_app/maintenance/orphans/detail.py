from pathlib import Path

from .models import OrphanCandidate


def show_orphan_detail(
    item: OrphanCandidate,
):

    print()

    print(
        "DECKFLIX ORPHAN REVIEW"
    )

    print(
        "══════════════════════"
    )

    print()

    print(
        "Classification:"
    )

    print(
        item.classification.value
    )

    print()

    print(
        "Path:"
    )

    print(
        item.path
    )

    print()

    print(
        "Reason:"
    )

    print(
        item.reason
    )

    print()

    print(
        "Detected files"
    )

    print(
        "───────────────"
    )

    print(
        f"Video files     : {item.video_files}"
    )

    print(
        f"Subtitles       : {item.subtitle_files}"
    )

    print(
        f"Images          : {item.image_files}"
    )

    print(
        f"Metadata        : {item.metadata_files}"
    )

    print(
        f"Junk files      : {item.junk_files}"
    )

    print()

    print(
        "[B] Back"
    )

    input(
        "Press Enter to continue..."
    )
