"""JSON persistence for the DeckFlix inventory index."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deckflix_app.inventory.models import Inventory, utc_now


class InventoryRepository:
    """Load and save an inventory without exposing its storage format."""

    def __init__(self, inventory_file: Path) -> None:
        self.inventory_file = Path(inventory_file)

    def exists(self) -> bool:
        return self.inventory_file.is_file()

    def load(self) -> Inventory:
        """Load the inventory or return a new empty inventory."""
        if not self.exists():
            return Inventory.empty()

        try:
            with self.inventory_file.open(
                "r",
                encoding="utf-8",
            ) as file_handle:
                data: dict[str, Any] = json.load(file_handle)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid inventory JSON: {self.inventory_file}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read inventory: {self.inventory_file}"
            ) from exc

        return Inventory.from_dict(data)

    def save(self, inventory: Inventory) -> None:
        """Atomically save the inventory as formatted JSON."""
        self.inventory_file.parent.mkdir(parents=True, exist_ok=True)

        inventory.updated = utc_now()

        temporary_file = self.inventory_file.with_suffix(
            self.inventory_file.suffix + ".tmp"
        )

        try:
            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file_handle:
                json.dump(
                    inventory.to_dict(),
                    file_handle,
                    indent=2,
                    sort_keys=True,
                )
                file_handle.write("\n")
                file_handle.flush()
                os.fsync(file_handle.fileno())

            temporary_file.replace(self.inventory_file)
        except OSError as exc:
            temporary_file.unlink(missing_ok=True)

            raise RuntimeError(
                f"Unable to save inventory: {self.inventory_file}"
            ) from exc

    def backup(self, backup_directory: Path | None = None) -> Path | None:
        """Create a timestamped inventory backup if an inventory exists."""
        if not self.exists():
            return None

        destination_directory = (
            Path(backup_directory)
            if backup_directory is not None
            else self.inventory_file.parent / "backups"
        )
        destination_directory.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_file = (
            destination_directory
            / f"{self.inventory_file.stem}-{timestamp}.json"
        )

        try:
            shutil.copy2(self.inventory_file, backup_file)
        except OSError as exc:
            raise RuntimeError(
                f"Unable to back up inventory: {self.inventory_file}"
            ) from exc

        return backup_file

    def validate(self) -> None:
        """Load and validate the stored inventory."""
        if not self.exists():
            raise FileNotFoundError(self.inventory_file)

        self.load()
