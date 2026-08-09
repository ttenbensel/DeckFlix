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
        "Reason:"
    )

    print(
        item.reason
    )

    print()

    print(
        "MEDIA"
    )

    print(
        "─────"
    )

    print(
        f"Title: {item.source.title}"
    )

    print(
        f"Year: {item.source.year}"
    )

    print()

    print(
        "SOURCE FILE"
    )

    print(
        "───────────"
    )

    print(
        item.source.path
    )

    print()

    print(
        f"Resolution : {item.source.resolution}"
    )

    print(
        f"Source     : {item.source.source}"
    )

    print(
        f"Codec      : {item.source.video_codec}"
    )

    print()

    print(
        "DESTINATION FILE"
    )

    print(
        "────────────────"
    )

    print(
        item.destination.path
    )

    print()

    print(
        f"Resolution : {item.destination.resolution}"
    )

    print(
        f"Source     : {item.destination.source}"
    )

    print(
        f"Codec      : {item.destination.video_codec}"
    )

    print()

    print(
        "RECOMMENDATION"
    )

    print(
        "──────────────"
    )

    if item.classification.value == "SOURCE_BETTER":

        print(
            "Source appears higher quality"
        )

        print(
            "Review upgrade opportunity"
        )


    elif item.classification.value == "DUPLICATE_MEDIA":

        print(
            "Destination appears equal or better"
        )

        print(
            "No upgrade required"
        )


    else:

        print(
            "Quality difference uncertain"
        )

        print(
            "Manual review recommended"
        )


    print()

    print(
        "[B] Back"
    )

    input(
        "Press Enter to continue..."
    )
