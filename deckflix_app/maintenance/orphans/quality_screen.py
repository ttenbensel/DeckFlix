from pathlib import Path

from .duplicate_scanner import scan_duplicates


def show_quality_detail(
    item,
):

    print()

    print(
        "QUALITY DETAIL"
    )

    print(
        "══════════════"
    )

    print()

    print(
        "MOVIE"
    )

    print(
        "─────"
    )

    print(
        f"{item.source.title}"
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
        f"Path:"
    )

    print(
        f"{item.source.path}"
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
        f"Path:"
    )

    print(
        f"{item.destination.path}"
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
        "CLASSIFICATION"
    )

    print(
        "──────────────"
    )

    print(
        item.classification.value
    )

    print()

    print(
        "REASON"
    )

    print(
        "──────"
    )

    print(
        item.reason
    )

    print()

    input(
        "Press Enter to continue..."
    )



def show_quality_list(
    title,
    items,
):

    while True:

        print()

        print(title)

        print(
            "─────────────"
        )


        if not items:

            print(
                "No items found"
            )

        else:

            for index, item in enumerate(
                items,
                start=1,
            ):

                print(
                    f"{index}. "
                    f"{item.source.title}"
                    f" ({item.source.year})"
                )


        print()

        print(
            "[B] Back"
        )


        choice = input(
            "Select item: "
        ).strip().lower()


        if choice == "b":
            return


        if choice.isdigit():

            number = int(choice)

            if (
                number >= 1
                and number <= len(items)
            ):

                show_quality_detail(
                    items[number - 1]
                )



def show_quality_review(
    source: Path,
    destination: Path,
):

    results = scan_duplicates(
        source,
        destination,
    )


    duplicate_media = [
        item
        for item in results
        if item.classification.value
        == "DUPLICATE_MEDIA"
    ]


    source_better = [
        item
        for item in results
        if item.classification.value
        == "SOURCE_BETTER"
    ]


    quality_review = [
        item
        for item in results
        if item.classification.value
        == "QUALITY_REVIEW"
    ]


    while True:

        print()

        print(
            "DECKFLIX QUALITY REVIEW"
        )

        print(
            "═══════════════════════"
        )

        print()

        print(
            f"Duplicate media : "
            f"{len(duplicate_media)}"
        )

        print(
            f"Source better   : "
            f"{len(source_better)}"
        )

        print(
            f"Quality review  : "
            f"{len(quality_review)}"
        )

        print()

        print(
            "[D] Duplicate media"
        )

        print(
            "[S] Source better"
        )

        print(
            "[Q] Quality review"
        )

        print(
            "[B] Back"
        )


        choice = input(
            "Select option: "
        ).strip().lower()


        if choice == "b":
            return


        elif choice == "d":

            show_quality_list(
                "DUPLICATE MEDIA",
                duplicate_media,
            )


        elif choice == "s":

            show_quality_list(
                "SOURCE BETTER",
                source_better,
            )


        elif choice == "q":

            show_quality_list(
                "QUALITY REVIEW",
                quality_review,
            )
