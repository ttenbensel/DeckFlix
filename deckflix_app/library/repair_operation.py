from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import os
from pathlib import Path
import shutil
from uuid import uuid4

from deckflix_app.config import DeckFlixConfig
from deckflix_app.importer.checksum import sha256

from .repair_journal import (
    LibraryRepairJournal,
    RepairJournalEntry,
    RepairJournalStatus,
)
from .repair_plan import (
    LibraryRepairAction,
    LibraryRepairPlan,
    LibraryRepairStatus,
)


class RepairOperationError(RuntimeError):
    """Base error for protected library repair operations."""


class RepairOperationTransitionError(
    RepairOperationError
):
    """Raised when a repair operation changes state illegally."""


class RepairOperationInvalidated(
    RepairOperationError
):
    """Raised when an approved repair has changed."""


class RepairOperationState(str, Enum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True, slots=True)
class RepairSourceSnapshot:
    source: Path
    size: int
    modified_ns: int
    checksum: str


@dataclass(frozen=True, slots=True)
class ApprovedRepair:
    source: Path
    destination: Path
    action: LibraryRepairAction
    reason: str
    plan_item_index: int
    snapshot: RepairSourceSnapshot


@dataclass(frozen=True, slots=True)
class RepairPreflightResult:
    operation_id: str
    plan_fingerprint: str
    approved_files: int
    approved_bytes: int
    source_missing: int
    source_changed: int
    destination_conflicts: int
    destination_not_writable: int
    invalid_items: int
    reasons: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return (
            self.approved_files > 0
            and self.source_missing == 0
            and self.source_changed == 0
            and self.destination_conflicts == 0
            and self.destination_not_writable == 0
            and self.invalid_items == 0
            and not self.reasons
        )


@dataclass(frozen=True, slots=True)
class RepairOperationResult:
    operation_id: str
    completed: int
    failed: int
    paused: bool
    entries: tuple[RepairJournalEntry, ...]

    @property
    def successful(self) -> bool:
        return (
            self.failed == 0
            and not self.paused
            and self.completed == len(self.entries)
        )


def _plan_fingerprint(
    plan: LibraryRepairPlan,
) -> str:
    digest = hashlib.sha256()

    for index, item in enumerate(
        plan.items
    ):
        parts = (
            str(index),
            str(item.source),
            str(item.destination),
            item.action.value,
            item.status.value,
            item.reason,
        )

        digest.update(
            "\x1f".join(parts).encode(
                "utf-8"
            )
        )
        digest.update(b"\n")

    return digest.hexdigest()


def _snapshot_source(
    source: Path,
) -> RepairSourceSnapshot:
    source = Path(source)

    if not source.exists():
        raise FileNotFoundError(source)

    stat = source.stat()

    return RepairSourceSnapshot(
        source=source,
        size=stat.st_size,
        modified_ns=stat.st_mtime_ns,
        checksum=sha256(source),
    )


def _source_matches_snapshot(
    snapshot: RepairSourceSnapshot,
) -> bool:
    try:
        stat = snapshot.source.stat()

        if stat.st_size != snapshot.size:
            return False

        if stat.st_mtime_ns != snapshot.modified_ns:
            return False

        return (
            sha256(snapshot.source)
            == snapshot.checksum
        )

    except (
        FileNotFoundError,
        OSError,
    ):
        return False


def _directory_writable(
    path: Path,
) -> bool:
    directory = Path(path)

    while not directory.exists():
        parent = directory.parent

        if parent == directory:
            return False

        directory = parent

    return directory.is_dir()


def _journal_entry(
    entry: RepairJournalEntry,
    *,
    status: RepairJournalStatus,
    destination_checksum: str | None = None,
    completed_at: datetime | None = None,
    error: str | None = None,
) -> RepairJournalEntry:
    return RepairJournalEntry(
        source=entry.source,
        destination=entry.destination,
        action=entry.action,
        reason=entry.reason,
        source_size=entry.source_size,
        source_modified_ns=entry.source_modified_ns,
        source_checksum=entry.source_checksum,
        status=status,
        destination_checksum=destination_checksum,
        completed_at=completed_at,
        error=error,
    )


def _temporary_destination(
    destination: Path,
    operation_id: str,
    index: int,
) -> Path:
    return destination.with_name(
        ".deckflix-repair-"
        f"{operation_id}-"
        f"{index:04d}-"
        f"{destination.name}.partial"
    )


def _copy_file(
    source: Path,
    destination: Path,
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )

    with destination.open(
        "rb"
    ) as handle:
        os.fsync(handle.fileno())


class RepairOperationManager:
    """
    Persistent lifecycle manager for one approved
    library repair operation.

    Approval creates immutable source fingerprints.

    Existing journals are automatically recovered.

    Review and blocked items are deliberately excluded
    from the executable operation.

    This manager performs no media writes itself.
    """

    def __init__(
        self,
        plan: LibraryRepairPlan,
        *,
        journal_path: Path,
        operation_id: str | None = None,
    ) -> None:
        self.plan = plan

        journal_path = Path(journal_path)

        existing_journal = (
            LibraryRepairJournal.load(
                journal_path
            )
        )

        if existing_journal is not None:
            if (
                operation_id is not None
                and operation_id
                != existing_journal.operation_id
            ):
                raise RepairOperationTransitionError(
                    "Journal operation ID does not "
                    "match the requested operation ID."
                )

            self.operation_id = (
                existing_journal.operation_id
            )

            self.journal = existing_journal

        else:
            self.operation_id = (
                operation_id
                or (
                    f"DR-{datetime.now():%Y%m%d-%H%M%S}-"
                    f"{uuid4().hex[:6].upper()}"
                )
            )

            self.journal = LibraryRepairJournal(
                journal_path,
                operation_id=self.operation_id,
            )

        self.plan_fingerprint = (
            _plan_fingerprint(plan)
        )

        persisted_fingerprint = (
            self.journal.plan_fingerprint
        )

        if persisted_fingerprint:
            self.plan_fingerprint = (
                persisted_fingerprint
            )

        self.approved_repairs: tuple[
            ApprovedRepair,
            ...
        ] = ()

        try:
            self.state = RepairOperationState(
                self.journal.state
            )
        except ValueError as exc:
            raise RepairOperationTransitionError(
                "Repair journal contains an "
                f"unknown state: {self.journal.state}"
            ) from exc

        self.write_authorized = (
            self.journal.write_authorized
        )

        if self.journal.entries:
            self.approved_repairs = (
                self._approved_from_journal()
            )

        if persisted_fingerprint:
            current_fingerprint = (
                _plan_fingerprint(plan)
            )

            if (
                current_fingerprint
                != persisted_fingerprint
            ):
                self.state = (
                    RepairOperationState.INVALIDATED
                )
                self.write_authorized = False

                self._persist()

                raise RepairOperationInvalidated(
                    "The current repair plan does not "
                    "match the persisted approved plan."
                )

        else:
            self.plan_fingerprint = (
                _plan_fingerprint(plan)
            )

            self.journal.plan_fingerprint = (
                self.plan_fingerprint
            )

    def _persist(self) -> None:
        self.journal.state = (
            self.state.value
        )
        self.journal.write_authorized = (
            self.write_authorized
        )
        self.journal.plan_fingerprint = (
            self.plan_fingerprint
        )
        self.journal.save()

    def approve(self) -> int:
        if self.state is not RepairOperationState.CREATED:
            raise RepairOperationTransitionError(
                "Repair operation can only be approved "
                "from CREATED state."
            )

        if not self.plan.items:
            raise RepairOperationTransitionError(
                "Repair plan is empty."
            )

        ready_items = [
            (
                index,
                item,
            )
            for index, item in enumerate(
                self.plan.items
            )
            if item.status
            is LibraryRepairStatus.READY
        ]

        if not ready_items:
            raise RepairOperationTransitionError(
                "Repair plan contains no READY items."
            )

        approved: list[
            ApprovedRepair
        ] = []

        for index, item in ready_items:
            if item.action not in {
                LibraryRepairAction.MOVE,
                LibraryRepairAction.MOVE_RENAME,
            }:
                raise RepairOperationTransitionError(
                    "Only MOVE and MOVE_RENAME are "
                    "supported."
                )

            if item.destination is None:
                raise RepairOperationTransitionError(
                    "READY repair has no destination."
                )

            snapshot = _snapshot_source(
                item.source
            )

            approved.append(
                ApprovedRepair(
                    source=item.source,
                    destination=item.destination,
                    action=item.action,
                    reason=item.reason,
                    plan_item_index=index,
                    snapshot=snapshot,
                )
            )

        self.approved_repairs = tuple(
            approved
        )

        self.journal.entries = [
            RepairJournalEntry(
                source=repair.source,
                destination=repair.destination,
                action=repair.action.value,
                reason=repair.reason,
                source_size=repair.snapshot.size,
                source_modified_ns=(
                    repair.snapshot.modified_ns
                ),
                source_checksum=(
                    repair.snapshot.checksum
                ),
            )
            for repair in approved
        ]

        self.plan_fingerprint = (
            _plan_fingerprint(self.plan)
        )

        self.state = (
            RepairOperationState.APPROVED
        )

        self.write_authorized = False

        self._persist()

        return len(approved)

    def validate_plan(self) -> bool:
        if (
            _plan_fingerprint(self.plan)
            != self.plan_fingerprint
        ):
            self.state = (
                RepairOperationState.INVALIDATED
            )
            self.write_authorized = False
            self._persist()
            return False

        return True

    def require_valid_plan(self) -> None:
        if not self.validate_plan():
            raise RepairOperationInvalidated(
                "The repair plan has changed since "
                "approval."
            )

    def _approved_from_journal(
        self,
    ) -> tuple[ApprovedRepair, ...]:
        repairs: list[
            ApprovedRepair
        ] = []

        for journal_index, entry in enumerate(
            self.journal.entries
        ):
            plan_item_index = journal_index

            for index, item in enumerate(
                self.plan.items
            ):
                if (
                    item.source == entry.source
                    and item.destination
                    == entry.destination
                    and item.action.value
                    == entry.action
                ):
                    plan_item_index = index
                    break

            repairs.append(
                ApprovedRepair(
                    source=entry.source,
                    destination=entry.destination,
                    action=LibraryRepairAction(
                        entry.action
                    ),
                    reason=entry.reason,
                    plan_item_index=plan_item_index,
                    snapshot=RepairSourceSnapshot(
                        source=entry.source,
                        size=entry.source_size,
                        modified_ns=(
                            entry.source_modified_ns
                        ),
                        checksum=(
                            entry.source_checksum
                        ),
                    ),
                )
            )

        return tuple(repairs)

    def final_preflight(
        self,
        progress_callback=None,
    ) -> RepairPreflightResult:
        if self.state not in {
            RepairOperationState.APPROVED,
            RepairOperationState.AUTHORIZED,
            RepairOperationState.EXECUTING,
        }:
            raise RepairOperationTransitionError(
                "Repair preflight requires an APPROVED, "
                "AUTHORIZED, or EXECUTING operation."
            )

        self.require_valid_plan()

        if not self.approved_repairs:
            self.approved_repairs = (
                self._approved_from_journal()
            )

        source_missing = 0
        source_changed = 0
        destination_conflicts = 0
        destination_not_writable = 0
        invalid_items = 0
        approved_bytes = 0

        reasons: list[str] = []
        destinations: set[Path] = set()

        total_repairs = len(
            self.approved_repairs
        )

        for repair_index, repair in enumerate(
            self.approved_repairs,
            start=1,
        ):
            source = repair.source
            destination = repair.destination

            if progress_callback is not None:
                progress_callback(
                    repair_index,
                    total_repairs,
                    repair,
                )

            approved_bytes += (
                repair.snapshot.size
            )

            if not source.exists():
                source_missing += 1
                reasons.append(
                    f"Source missing: {source}"
                )
                continue

            if not _source_matches_snapshot(
                repair.snapshot
            ):
                source_changed += 1
                reasons.append(
                    "Source changed since approval: "
                    f"{source}"
                )

            if destination in destinations:
                invalid_items += 1
                reasons.append(
                    "Multiple approved repairs use "
                    f"destination: {destination}"
                )

            destinations.add(destination)

            if destination.exists():
                destination_conflicts += 1
                reasons.append(
                    "Destination already exists: "
                    f"{destination}"
                )

            if not _directory_writable(
                destination.parent
            ):
                destination_not_writable += 1
                reasons.append(
                    "Destination directory is not "
                    f"available: {destination.parent}"
                )

        return RepairPreflightResult(
            operation_id=self.operation_id,
            plan_fingerprint=self.plan_fingerprint,
            approved_files=len(
                self.approved_repairs
            ),
            approved_bytes=approved_bytes,
            source_missing=source_missing,
            source_changed=source_changed,
            destination_conflicts=(
                destination_conflicts
            ),
            destination_not_writable=(
                destination_not_writable
            ),
            invalid_items=invalid_items,
            reasons=tuple(reasons),
        )

    def authorize(
        self,
        config: DeckFlixConfig,
    ) -> RepairPreflightResult:
        if self.state is not RepairOperationState.APPROVED:
            raise RepairOperationTransitionError(
                "Repair Mode can only be enabled "
                "for an APPROVED operation."
            )

        result = self.final_preflight(
            progress_callback=None,
        )

        if not result.ready:
            raise RepairOperationTransitionError(
                "Final repair preflight failed: "
                + "; ".join(
                    result.reasons
                )
            )

        self.write_authorized = True
        self.state = (
            RepairOperationState.AUTHORIZED
        )

        self._persist()

        return result

    def begin_execution(self) -> None:
        if self.state is not RepairOperationState.AUTHORIZED:
            raise RepairOperationTransitionError(
                "Repair execution requires explicit "
                "Repair Mode authorization."
            )

        self.require_valid_plan()

        self.state = (
            RepairOperationState.EXECUTING
        )

        self._persist()

    def pause(self) -> None:
        if self.state is not RepairOperationState.EXECUTING:
            raise RepairOperationTransitionError(
                "Only an executing repair can be paused."
            )

        self.state = (
            RepairOperationState.PAUSED
        )
        self.write_authorized = False

        self._persist()

    def complete(self) -> None:
        if self.state is not RepairOperationState.EXECUTING:
            raise RepairOperationTransitionError(
                "Only an executing repair can complete."
            )

        self.state = (
            RepairOperationState.COMPLETE
        )
        self.write_authorized = False

        self._persist()

    def fail(self) -> None:
        self.state = (
            RepairOperationState.FAILED
        )
        self.write_authorized = False

        self._persist()

    def revoke_authorization(self) -> None:
        self.write_authorized = False

        if self.state is (
            RepairOperationState.AUTHORIZED
        ):
            self.state = (
                RepairOperationState.APPROVED
            )

        self._persist()


class LibraryRepairExecutor:
    """
    Protected filesystem executor.

    Execution order for each repair:

        1. Verify the approved source fingerprint.
        2. Verify the destination does not exist.
        3. Record COPYING in the journal.
        4. Copy the source to a temporary destination.
        5. Verify SHA-256 of the temporary copy.
        6. Re-check the source fingerprint.
        7. Atomically publish the destination.
        8. Remove the original source.
        9. Record VERIFIED.

    Existing destinations are never overwritten.

    Temporary copies remain beside the destination if an
    operation is interrupted. They are never treated as a
    completed repair.
    """

    def execute(
        self,
        manager: RepairOperationManager,
        *,
        config: DeckFlixConfig,
    ) -> RepairOperationResult:
        if not manager.write_authorized:
            raise RepairOperationTransitionError(
                "Repair Mode has not been enabled."
            )

        if manager.state is not RepairOperationState.AUTHORIZED:
            raise RepairOperationTransitionError(
                "Repair execution requires an "
                "AUTHORIZED operation."
            )

        manager.begin_execution()

        completed = sum(
            1
            for entry in manager.journal.entries
            if entry.status
            is RepairJournalStatus.VERIFIED
        )

        failed = 0

        try:
            final_preflight = (
                manager.final_preflight()
            )

            if not final_preflight.ready:
                error_message = (
                    "Final repair preflight failed: "
                    + "; ".join(
                        final_preflight.reasons
                    )
                )

                for index, entry in enumerate(
                    manager.journal.entries
                ):
                    if entry.status is (
                        RepairJournalStatus.VERIFIED
                    ):
                        continue

                    manager.journal.entries[index] = (
                        _journal_entry(
                            entry,
                            status=(
                                RepairJournalStatus.FAILED
                            ),
                            error=error_message,
                        )
                    )

                manager._persist()
                manager.fail()

                raise RepairOperationInvalidated(
                    error_message
                )

            for index, entry in enumerate(
                manager.journal.entries
            ):
                if entry.status is (
                    RepairJournalStatus.VERIFIED
                ):
                    continue

                repair = (
                    manager.approved_repairs[index]
                )

                source = repair.source
                destination = repair.destination

                if not _source_matches_snapshot(
                    repair.snapshot
                ):
                    manager.journal.entries[index] = (
                        _journal_entry(
                            entry,
                            status=(
                                RepairJournalStatus.FAILED
                            ),
                            error=(
                                "Source changed after "
                                "final preflight."
                            ),
                        )
                    )
                    manager._persist()
                    failed += 1
                    manager.fail()
                    break

                if destination.exists():
                    manager.journal.entries[index] = (
                        _journal_entry(
                            entry,
                            status=(
                                RepairJournalStatus.FAILED
                            ),
                            error=(
                                "Destination appeared "
                                "after final preflight."
                            ),
                        )
                    )
                    manager._persist()
                    failed += 1
                    manager.fail()
                    break

                temporary = _temporary_destination(
                    destination,
                    manager.operation_id,
                    index,
                )

                if temporary.exists():
                    manager.journal.entries[index] = (
                        _journal_entry(
                            entry,
                            status=(
                                RepairJournalStatus.FAILED
                            ),
                            error=(
                                "Temporary repair "
                                "destination already exists: "
                                f"{temporary}"
                            ),
                        )
                    )
                    manager._persist()
                    failed += 1
                    manager.fail()
                    break

                manager.journal.entries[index] = (
                    _journal_entry(
                        entry,
                        status=(
                            RepairJournalStatus.COPYING
                        ),
                    )
                )
                manager._persist()

                try:
                    _copy_file(
                        source,
                        temporary,
                    )

                    temporary_checksum = sha256(
                        temporary
                    )

                    if (
                        temporary_checksum
                        != repair.snapshot.checksum
                    ):
                        raise RepairOperationError(
                            "Destination checksum does not "
                            "match approved source."
                        )

                    if not _source_matches_snapshot(
                        repair.snapshot
                    ):
                        raise RepairOperationInvalidated(
                            "Source changed after copy "
                            "verification."
                        )

                    if destination.exists():
                        raise RepairOperationError(
                            "Destination appeared before "
                            "publication."
                        )

                    temporary.replace(
                        destination
                    )

                    destination_checksum = (
                        sha256(destination)
                    )

                    if (
                        destination_checksum
                        != repair.snapshot.checksum
                    ):
                        raise RepairOperationError(
                            "Published destination checksum "
                            "does not match approved source."
                        )

                    if not _source_matches_snapshot(
                        repair.snapshot
                    ):
                        raise RepairOperationInvalidated(
                            "Source changed after destination "
                            "publication."
                        )

                    source.unlink()

                    manager.journal.entries[index] = (
                        _journal_entry(
                            entry,
                            status=(
                                RepairJournalStatus.VERIFIED
                            ),
                            destination_checksum=(
                                destination_checksum
                            ),
                            completed_at=datetime.now(),
                        )
                    )
                    manager._persist()

                    completed += 1

                except BaseException as exc:
                    if temporary.exists():
                        try:
                            temporary.unlink()
                        except OSError:
                            pass

                    manager.journal.entries[index] = (
                        _journal_entry(
                            entry,
                            status=(
                                RepairJournalStatus.FAILED
                            ),
                            error=str(exc),
                        )
                    )
                    manager._persist()

                    failed += 1
                    manager.fail()
                    raise

            if failed == 0:
                manager.complete()

            return RepairOperationResult(
                operation_id=manager.operation_id,
                completed=completed,
                failed=failed,
                paused=False,
                entries=tuple(
                    manager.journal.entries
                ),
            )

        except BaseException:
            if manager.state is (
                RepairOperationState.EXECUTING
            ):
                manager.pause()

            raise
