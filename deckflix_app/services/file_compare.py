from deckflix_app.services.recommendation_engine import (
    recommend_duplicate_group,
)


def bytes_to_gb(value):
    return value / 1024**3


def compare_release_files(release):
    """
    Build a read-only comparison of every file in a release.
    """

    recommendation = recommend_duplicate_group(release.copies)

    keep = recommendation["keep"]
    equivalent = recommendation["equivalent_copies"]
    alternatives = recommendation["alternatives"]

    confirmed_equivalent = (
        equivalent
        if release.confirmed
        else []
    )

    return {
        "keep": keep,
        "equivalent": equivalent,
        "alternatives": alternatives,
        "confirmed": release.confirmed,
        "confirmed_sha256": release.confirmed_sha256,
        "recoverable_bytes": sum(
            item.size
            for item in confirmed_equivalent
        ),
    }


def show_file_comparison(result):
    """
    Display a read-only comparison report.
    """

    print()
    print("Compare Files")
    print("═════════════")

    keep = result["keep"]

    print()
    print("KEEP")
    print("────")
    print(keep.path)
    print(f"Size: {bytes_to_gb(keep.size):.2f} GB")
    print(
        f"Media: {keep.resolution} | {keep.source} | "
        f"{keep.codec} | score {keep.quality_score}"
    )

    if result["equivalent"]:
        print()
        print("EQUIVALENT COPIES")
        print("─────────────────")

        for item in result["equivalent"]:
            print(item.path)
            print(f"Size: {bytes_to_gb(item.size):.2f} GB")

            if result["confirmed"]:
                print("SHA-256: Confirmed byte-identical")
            else:
                print("SHA-256: Not confirmed")

            print()

    if result["alternatives"]:
        print("ALTERNATIVE RELEASES")
        print("────────────────────")

        for item in result["alternatives"]:
            print(item.path)
            print(
                f"{item.resolution} | {item.source} | "
                f"{item.codec} | score {item.quality_score} | "
                f"{bytes_to_gb(item.size):.2f} GB"
            )
            print()

    print("Recoverable Space")
    print("─────────────────")
    print(f"{bytes_to_gb(result['recoverable_bytes']):.2f} GB")

    print()
    print("Read-only. Nothing has been changed.")
