from pathlib import Path

from deckflix_app.system_verification import (
    run_system_verification,
)


def show_ship_status(
    *,
    config,
    operation_manager,
) -> None:

    result = run_system_verification(
        config=config,
        operation_manager=operation_manager,
        temp_directory=Path(
            str(
                config.import_staging_directory
            )
        ),
    )


    print()

    print(
        "DECKFLIX SHIP STATUS"
    )

    print(
        "════════════════════"
    )


    print()

    print(
        "OPERATING MODE"
    )

    print(
        "──────────────"
    )

    print(
        f"Profile        "
        f"{config.operating_profile}"
    )

    print(
        f"Low Impact     "
        f"{'Enabled' if config.low_impact else 'Off'}"
    )

    print(
        f"Write Protect  "
        f"{'Enabled' if config.read_only else 'Off'}"
    )

    print(
        f"Network        "
        f"{'Offline' if config.operating_profile == 'ship_offline' else 'Restricted' if config.operating_profile == 'ship_limited' else 'Normal'}"
    )


    print()

    print(
        "SYSTEM CHECKS"
    )

    print(
        "─────────────"
    )


    for check in result.checks:

        status = (
            "PASS"
            if check.passed
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{check.name:<32}"
            f"{check.detail}"
        )


    print()

    print(
        "SUMMARY"
    )

    print(
        "───────"
    )

    print(
        f"Passed       {result.passed}"
    )

    print(
        f"Failed       {result.failed}"
    )


    print()

    print(
        "SHIP READINESS"
    )

    print(
        "──────────────"
    )


    if result.ready:

        print(
            "READY FOR OPERATION"
        )

    else:

        print(
            "ACTION REQUIRED"
        )


    print()

    input(
        "Press Enter to return..."
    )
