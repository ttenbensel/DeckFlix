from pathlib import Path

from .bridge import (
    create_upgrade_from_quality,
)

from .screen import (
    show_upgrade_review,
)


def create_upgrade_menu(
    item,
):

    upgrade = create_upgrade_from_quality(
        item
    )

    show_upgrade_review(
        upgrade,
        Path(
            "/data/library1/"
            "deckflix-logs/"
            "upgrades/"
            "upgrade-history.json"
        ),
    )
