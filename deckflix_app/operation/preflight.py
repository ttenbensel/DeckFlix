from dataclasses import dataclass, field
from pathlib import Path
import json
import shutil
import tempfile

from deckflix_app.decision import (
    ApprovalStatus,
)
from deckflix_app.importer.checksum import (
    verify,
)
from deckflix_app.importer.journal import (
    load_import_journal,
)

from .destination import (
    destination_for_media,
)

from .manager import (
    InvalidOperationTransition,
    OperationManager,
)


@dataclass(frozen=True, slots=True)
class PreflightConflict:
    source: Path
    destination: Path
    reason: str


@dataclass(slots=True)
class ImportPreflightResult:
    approved_files: int = 0
    approved_bytes: int = 0

    movie_bytes: int = 0
    tv_bytes: int = 0

    movie_free_bytes: int = 0
    tv_free_bytes: int = 0

    missing_sources: list[Path] = field(
        default_factory=list
    )
    changed_sources: list[Path] = field(
        default_factory=list
    )
    conflicts: list[PreflightConflict] = field(
        default_factory=list
    )
    errors: list[str] = field(
        default_factory=list
    )

    review_items: int = 0
    skipped_items: int = 0
    snapshot_valid: bool = False
    movie_library_writable: bool = False
    tv_library_writable: bool = False
    temp_writable: bool = False

    @property
    def ready(self) -> bool:
        return all(
            [
                self.approved_files > 0,
                self.snapshot_valid,
                not self.missing_sources,
                not self.changed_sources,
                not self.conflicts,
                not self.errors,
                self.movie_library_writable,
                self.tv_library_writable,
                self.temp_writable,
                self.movie_free_bytes >= self.movie_bytes,
                self.tv_free_bytes >= self.tv_bytes,
            ]
        )


def _directory_is_writable(path: Path) -> bool:
    path = Path(path)

    try:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            prefix=".deckflix-write-test-",
            dir=path,
            delete=True,
        ):
            pass

        return True

    except OSError:
        return False


def _resume_entries(
    journal_path: Path | None,
    *,
    operation_id: str,
) -> dict[Path, object]:
    """
    Load resumable import evidence for this exact operation.

    A journal from another operation is never trusted.

    Entry destinations are indexed by resolved path, but individual
    source/destination identity and file content are still verified
    before preflight treats an existing destination as resumable.
    """
    if journal_path is None:
        return {}

    journal_path = Path(journal_path)

    if not journal_path.exists():
        return {}

    try:
        journal = load_import_journal(
            journal_path
        )

    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ):
        return {}

    if (
        journal is None
        or journal.operation_id != operation_id
    ):
        return {}

    entries = {}

    for entry in journal.entries.values():
        try:
            destination = (
                Path(entry.destination)
                .resolve()
            )
        except (OSError, ValueError):
            continue

        entries[destination] = entry

    return entries


def _destination_is_resumable(
    *,
    source: Path,
    destination: Path,
    resume_entries: dict[Path, object],
) -> bool:
    """
    Return True only when an existing destination is backed by the
    active operation journal and still matches its shuttle source.

    The resumable executor deliberately reconciles COMPLETED,
    PENDING and FAILED journal states by checksum. PENDING/FAILED
    support is required for a process interruption after the atomic
    destination move but before the journal status was updated.
    """
    source = Path(source).resolve()
    destination = Path(
        destination
    ).resolve()

    entry = resume_entries.get(
        destination
    )

    if entry is None:
        return False

    try:
        journal_source = (
            Path(entry.source)
            .resolve()
        )
        journal_destination = (
            Path(entry.destination)
            .resolve()
        )
    except (OSError, ValueError):
        return False

    if journal_source != source:
        return False

    if journal_destination != destination:
        return False

    if not destination.exists():
        return False

    try:
        return verify(
            source,
            destination,
        )
    except OSError:
        return False


def _source_matches_snapshot(
    source: Path,
    *,
    shuttle_path: Path,
    snapshot_lookup: dict[Path, object],
) -> bool:
    try:
        relative = source.relative_to(
            shuttle_path
        )
        expected = snapshot_lookup[relative]
        current = source.stat()

    except (
        KeyError,
        FileNotFoundError,
        OSError,
        ValueError,
    ):
        return False

    return (
        current.st_size == expected.size
        and current.st_mtime_ns
        == expected.modified_ns
    )


def run_import_preflight(
    manager: OperationManager,
    *,
    movie_library: Path,
    tv_library: Path,
    temp_dir: Path,
    journal_path: Path | None = None,
) -> ImportPreflightResult:
    operation = manager.require_operation()

    if manager.approval_plan is None:
        raise InvalidOperationTransition(
            "No approval plan is attached"
        )

    result = ImportPreflightResult()

    resume_entries = _resume_entries(
        journal_path,
        operation_id=operation.id,
    )

    result.snapshot_valid = (
        manager.validate_snapshot()
    )

    if not result.snapshot_valid:
        result.errors.append(
            "Shuttle snapshot is no longer valid"
        )
        return result

    movie_library = Path(
        movie_library
    )
    tv_library = Path(
        tv_library
    )
    temp_dir = Path(temp_dir)

    result.movie_library_writable = (
        _directory_is_writable(
            movie_library
        )
    )
    result.tv_library_writable = (
        _directory_is_writable(
            tv_library
        )
    )
    result.temp_writable = (
        _directory_is_writable(
            temp_dir
        )
    )

    try:
        result.movie_free_bytes = (
            shutil.disk_usage(
                movie_library
            ).free
        )
    except OSError as exc:
        result.errors.append(
            f"Movie library storage check failed: {exc}"
        )

    try:
        result.tv_free_bytes = (
            shutil.disk_usage(
                tv_library
            ).free
        )
    except OSError as exc:
        result.errors.append(
            f"TV library storage check failed: {exc}"
        )

    plan = manager.approval_plan

    result.review_items = plan.count(
        ApprovalStatus.REVIEW
    )
    result.skipped_items = plan.count(
        ApprovalStatus.SKIPPED
    )

    snapshot_lookup = {
        item.relative_path: item
        for item in operation.snapshot.files
    }

    for approval in plan.approved():
        media = approval.queue_item.incoming
        source = media.path

        if source is None:
            result.errors.append(
                f"Approved item has no source path: "
                f"{media.title}"
            )
            continue

        source = Path(source)

        result.approved_files += 1

        try:
            source_size = source.stat().st_size
            result.approved_bytes += source_size
        except OSError:
            result.missing_sources.append(
                source
            )
            continue

        if not _source_matches_snapshot(
            source,
            shuttle_path=(
                operation.snapshot.shuttle_path
            ),
            snapshot_lookup=snapshot_lookup,
        ):
            result.changed_sources.append(
                source
            )
            continue

        try:
            destination = destination_for_media(
                media,
                movie_library=movie_library,
                tv_library=tv_library,
            )
        except Exception as exc:
            result.errors.append(
                f"{source}: {exc}"
            )
            continue

        # Existing destinations are accepted only when the active
        # operation journal identifies this exact source/destination
        # pair and the destination still verifies against the source.
        #
        # This preserves safe interruption recovery without allowing
        # an unrelated stale destination to bypass preflight.
        if _destination_is_resumable(
            source=source,
            destination=destination,
            resume_entries=resume_entries,
        ):
            continue

        if media.media_type == "tv":
            result.tv_bytes += source_size
        else:
            result.movie_bytes += source_size

        if destination.exists():
            result.conflicts.append(
                PreflightConflict(
                    source=source,
                    destination=destination,
                    reason=(
                        "Destination already exists"
                    ),
                )
            )

    if not result.movie_library_writable:
        result.errors.append(
            "Movie library is not writable"
        )

    if not result.tv_library_writable:
        result.errors.append(
            "TV library is not writable"
        )

    if not result.temp_writable:
        result.errors.append(
            "Temporary import directory is not writable"
        )

    if (
        result.movie_free_bytes
        < result.movie_bytes
    ):
        result.errors.append(
            "Insufficient free space in movie library"
        )

    if (
        result.tv_free_bytes
        < result.tv_bytes
    ):
        result.errors.append(
            "Insufficient free space in TV library"
        )

    return result
