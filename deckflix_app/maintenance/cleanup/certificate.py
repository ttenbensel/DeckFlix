from .journal import CleanupJournal


def print_cleanup_certificate(
    journal: CleanupJournal,
):

    verified = sum(
        1
        for entry in journal.entries
        if entry.status.value == "VERIFIED"
    )

    failed = sum(
        1
        for entry in journal.entries
        if entry.status.value == "FAILED"
    )

    print()

    print(
        "DECKFLIX CLEANUP CERTIFICATE"
    )

    print(
        "═══════════════════════════"
    )

    print()

    print(
        f"Actions   : {len(journal.entries)}"
    )

    print(
        f"Verified  : {verified}"
    )

    print(
        f"Failed    : {failed}"
    )

    print()

    if failed == 0:
        print(
            "Result    : COMPLETE"
        )
    else:
        print(
            "Result    : REVIEW REQUIRED"
        )

    print()

    print(
        "Journal:"
    )

    print(
        journal.path
    )

    print()
