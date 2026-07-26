from deckflix_app.models.cleanup_plan import CleanupPlan
from deckflix_app.services.recommendation_engine import (
    recommend_duplicate_group,
)


def build_cleanup_plan(release):
    """
    Build a read-only cleanup proposal for one media release.

    Exact duplicates may be proposed for quarantine only after
    SHA-256 confirmation. Alternate releases are always left alone.
    """

    recommendation = recommend_duplicate_group(release.copies)

    keep = recommendation["keep"]
    equivalent = recommendation["equivalent_copies"]
    alternatives = recommendation["alternatives"]

    quarantine = []
    leave = list(alternatives)
    reasons = []

    if release.confirmed:
        quarantine = list(equivalent)

        if quarantine:
            reasons.append(
                "Equivalent copies confirmed byte-identical by SHA-256"
            )
    else:
        leave.extend(equivalent)

        if equivalent:
            reasons.append(
                "Equivalent-ranked copies are not SHA-256 confirmed"
            )

    if alternatives:
        reasons.append(
            "Alternate releases are preserved for manual review"
        )

    recovered_bytes = sum(
        item.size
        for item in quarantine
    )

    risk = "LOW" if quarantine and release.confirmed else "REVIEW"

    if not reasons:
        reasons.append("No safe cleanup action identified")

    return CleanupPlan(
        release_key=release.key,
        keep=[keep],
        quarantine=quarantine,
        leave=leave,
        recovered_bytes=recovered_bytes,
        risk=risk,
        reasons=reasons,
    )


def show_cleanup_plan(plan):
    """
    Display a read-only cleanup simulation.
    """

    title, year, _ = plan.release_key

    print()
    print("Simulated Cleanup")
    print("═════════════════")

    print()
    print(f"{title.title()} ({year or 'unknown'})")

    print()
    print("KEEP")
    print("────")
    for item in plan.keep:
        print(item.path)

    print()
    print("QUARANTINE")
    print("──────────")
    if plan.quarantine:
        for item in plan.quarantine:
            print(item.path)
    else:
        print("None")

    print()
    print("LEAVE UNCHANGED")
    print("───────────────")
    if plan.leave:
        for item in plan.leave:
            print(item.path)
    else:
        print("None")

    print()
    print("Reasons")
    print("───────")
    for reason in plan.reasons:
        print(f"• {reason}")

    print()
    print("Recoverable Space")
    print("─────────────────")
    print(f"{plan.recovered_gb:.2f} GB")

    print()
    print("Risk")
    print("────")
    print(plan.risk)

    print()
    print("Simulation only. Nothing has been changed.")
