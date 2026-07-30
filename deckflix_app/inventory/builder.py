"""Inventory construction for DeckFlix."""

from __future__ import annotations

from deckflix_app.inventory.models import Inventory
from deckflix_app.inventory.scan_result import ScanResult


class InventoryBuilder:
    """Construct an Inventory from a ScanResult."""

    def build(self, result: ScanResult) -> Inventory:
        """Build an inventory from raw scan results."""
        inventory = Inventory.empty()

        inventory.drives.extend(result.drives)
        inventory.libraries.extend(result.libraries)
        inventory.media.extend(result.media)

        inventory.last_scan = result.record

        if result.record is not None:
            inventory.updated = result.record.finished

        return inventory
