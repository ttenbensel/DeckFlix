from deckflix_app.services.recommendation_engine import (
    recommend_duplicate_group,
)


def build_release_report(release):
    """
    Build a read-only report for one provisional media release.
    """

    recommendation = recommend_duplicate_group(release.copies)

    reasons = list(recommendation["reasons"])
    confidence = recommendation["confidence"]

    if release.confirmed:
        reasons = [
            reason
            for reason in reasons
            if "confirm with SHA-256" not in reason
        ]
        reasons.insert(0, "Copies confirmed byte-identical by SHA-256")
        confidence = max(confidence, 100)


    confirmed_duplicates = []

    if release.confirmed and release.copy_count > 1:
        confirmed_duplicates = list(release.copies[1:])

    recoverable_bytes = sum(
        item.size
        for item in confirmed_duplicates
    )

    return {
        "key": release.key,
        "representative": release.representative,
        "copy_count": release.copy_count,
        "confirmed": release.confirmed,
        "confirmed_sha256": release.confirmed_sha256,
        "keep": recommendation["keep"],
        "equivalent_copies": recommendation["equivalent_copies"],
        "alternatives": recommendation["alternatives"],
        "reasons": reasons,
        "confidence": confidence,
        "confirmed_duplicates": confirmed_duplicates,
        "recoverable_bytes": recoverable_bytes,
    }


def show_release_report(report):
    """
    Print one release report to the terminal.
    """

    title, year, _ = report["key"]

    print()
    print("Release Inspector")
    print("═════════════════")
    print()
    print(f"{title.title()} ({year or 'unknown'})")
    print()

    print("Status")
    print("──────")
    print(f"Files               {report['copy_count']}")
    print(
        "Fingerprint         "
        + (
            "Confirmed exact match"
            if report["confirmed"]
            else "Not fully confirmed"
        )
    )
    print(f"Confidence          {report['confidence']}%")

    print()
    print("Recommended Keep")
    print("────────────────")
    keep = report["keep"]
    print(keep.path)
    print(
        f"{keep.resolution} | {keep.source} | "
        f"{keep.codec} | score {keep.quality_score}"
    )

    if report["equivalent_copies"]:
        print()
        print("Equivalent Copies")
        print("─────────────────")
        for item in report["equivalent_copies"]:
            print(item.path)

    if report["alternatives"]:
        print()
        print("Alternate Releases")
        print("──────────────────")
        for item in report["alternatives"]:
            print(
                f"{item.resolution:8} "
                f"{item.source:8} "
                f"score {item.quality_score:3}  "
                f"{item.path}"
            )

    print()
    print("Reasons")
    print("───────")
    for reason in report["reasons"]:
        print(f"• {reason}")

    print()
    print("Recoverable Space")
    print("─────────────────")
    print(f"{report['recoverable_bytes'] / 1024**3:.2f} GB")
    print()
    print("Read-only report. Nothing has been changed.")
