from .models import CleanupReport


def print_cleanup_report(
    report: CleanupReport,
):

    print()

    print(
        "DECKFLIX SOURCE CLEANUP"
    )

    print(
        "═══════════════════════"
    )

    print()

    print(
        f"Path:"
    )

    print(
        report.path
    )

    print()

    print(
        f"Video files      : {report.video_files}"
    )

    print(
        f"Subtitle files   : {report.subtitle_files}"
    )

    print(
        f"Images           : {report.image_files}"
    )

    print(
        f"Metadata         : {report.metadata_files}"
    )

    print(
        f"Other files      : {report.other_files}"
    )

    print(
        f"Empty directories: {report.empty_directories}"
    )

    print()

    print(
        f"Total size       : {report.total_bytes:,} bytes"
    )

    print()


    if report.other_examples:

        print(
            "OTHER FILE EXAMPLES"
        )

        print(
            "───────────────────"
        )

        for item in report.other_examples:

            print(
                item
            )

        print()


    if report.subtitle_examples:

        print(
            "SUBTITLE EXAMPLES"
        )

        print(
            "─────────────────"
        )

        for item in report.subtitle_examples[:5]:

            print(
                item
            )

        print()
