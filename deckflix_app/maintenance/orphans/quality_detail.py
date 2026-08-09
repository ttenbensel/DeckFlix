from .duplicates import DuplicateCandidate


def show_quality_detail(
    item: DuplicateCandidate,
):

    print()

    print(
        "DECKFLIX QUALITY REVIEW"
    )

    print(
        "═══════════════════════"
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
        "Title:"
    )

    print(
        item.source.title
    )

    if item.source.year:

        print(
            f"Year: {item.source.year}"
        )

    print()


    print(
        "SOURCE MEDIA"
    )

    print(
        "────────────"
    )

    print(
        "Path:"
    )

    print(
        item.source.path
    )

    print()

    print(
        f"Resolution : "
        f"{item.source.resolution or 'Unknown'}"
    )

    print(
        f"Source     : "
        f"{item.source.source or 'Unknown'}"
    )

    print(
        f"Codec      : "
        f"{item.source.video_codec or 'Unknown'}"
    )


    print()


    print(
        "DESTINATION MEDIA"
    )

    print(
        "─────────────────"
    )

    print(
        "Path:"
    )

    print(
        item.destination.path
    )

    print()

    print(
        f"Resolution : "
        f"{item.destination.resolution or 'Unknown'}"
    )

    print(
        f"Source     : "
        f"{item.destination.source or 'Unknown'}"
    )

    print(
        f"Codec      : "
        f"{item.destination.video_codec or 'Unknown'}"
    )


    print()


    print(
        "RECOMMENDATION"
    )

    print(
        "──────────────"
    )

    print(
        item.reason
    )


    print()

    print(
        "[B] Back"
    )

    input(
        "Press Enter to continue..."
    )
