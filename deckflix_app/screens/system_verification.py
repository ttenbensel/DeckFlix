from deckflix_app.system_verification import (
    SystemVerificationResult,
)


def show_system_verification(
    result: SystemVerificationResult,
) -> None:
    print()
    print("DeckFlix System Verification")
    print("════════════════════════════")

    for check in result.checks:
        status = "PASS" if check.passed else "FAIL"

        print(
            f"[{status}] "
            f"{check.name:<32} "
            f"{check.detail}"
        )

    print()
    print("Summary")
    print("───────")
    print(f"Passed              {result.passed}")
    print(f"Failed              {result.failed}")

    print()
    print("Overall Status")
    print("──────────────")

    if result.ready:
        print("SYSTEM READY")
    else:
        print("ACTION REQUIRED")

    print()
    print("No media files have been changed.")
