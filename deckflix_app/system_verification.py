from dataclasses import dataclass
from pathlib import Path
import tempfile

from deckflix_app.importer import (
    ImportJournal,
    JournalEntry,
    JournalStatus,
    load_import_journal,
    save_import_journal,
)

from deckflix_app.operation import (
    OperationManager,
    snapshot_files,
    snapshot_fingerprint,
)


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    name: str
    passed: bool
    detail: str


@dataclass(slots=True)
class SystemVerificationResult:
    checks: list[VerificationCheck]

    @property
    def passed(self) -> int:
        return sum(
            1
            for check in self.checks
            if check.passed
        )

    @property
    def failed(self) -> int:
        return sum(
            1
            for check in self.checks
            if not check.passed
        )

    @property
    def ready(self) -> bool:
        return self.failed == 0


def _path_exists_check(
    name: str,
    path: Path,
) -> VerificationCheck:

    path = Path(path)

    return VerificationCheck(
        name=name,
        passed=path.exists(),
        detail=str(path),
    )


def _directory_writable_check(
    name: str,
    path: Path,
) -> VerificationCheck:

    path = Path(path)

    try:

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            prefix=".deckflix-verify-",
            dir=path,
            delete=True,
        ):
            pass

        passed = True
        detail = str(path)

    except OSError as exc:

        passed = False
        detail = f"{path}: {exc}"


    return VerificationCheck(
        name=name,
        passed=passed,
        detail=detail,
    )


def _ship_mode_checks(
    config,
) -> list[VerificationCheck]:

    return [

        VerificationCheck(
            name="Operating profile",
            passed=(
                config.operating_profile
                in {
                    "normal",
                    "ship_limited",
                    "ship_offline",
                }
            ),
            detail=config.operating_profile,
        ),

        VerificationCheck(
            name="Low impact mode",
            passed=True,
            detail=(
                "Enabled"
                if config.low_impact
                else "Disabled"
            ),
        ),

        VerificationCheck(
            name="Network policy",
            passed=True,
            detail=(
                "Offline"
                if config.operating_profile
                == "ship_offline"
                else "Restricted"
                if config.operating_profile
                == "ship_limited"
                else "Normal"
            ),
        ),
    ]


def _snapshot_engine_check() -> VerificationCheck:

    try:

        with tempfile.TemporaryDirectory(
            prefix="deckflix-snapshot-check-"
        ) as temporary:

            root = Path(temporary)

            media = root / "movie.mkv"

            media.write_bytes(
                b"deckflix verification"
            )


            files = snapshot_files(
                root
            )

            fingerprint = snapshot_fingerprint(
                files
            )

            total_bytes = sum(
                item.size
                for item in files
            )


            passed = (
                len(files) == 1
                and total_bytes
                == len(
                    b"deckflix verification"
                )
                and len(fingerprint)
                == 64
            )


            detail = (
                f"{len(files)} file, "
                f"fingerprint "
                f"{fingerprint[:12]}..."
            )


    except Exception as exc:

        passed = False
        detail = str(exc)


    return VerificationCheck(
        name="Snapshot engine",
        passed=passed,
        detail=detail,
    )


def _journal_engine_check() -> VerificationCheck:

    try:

        with tempfile.TemporaryDirectory(
            prefix="deckflix-journal-check-"
        ) as temporary:

            destination = (
                Path(temporary)
                / "journal.json"
            )


            journal = ImportJournal(
                operation_id="DF-VERIFY-001",
                created_at="2026-08-01T00:00:00",
                updated_at="2026-08-01T00:00:00",
                entries={
                    "/library/movie.mkv": JournalEntry(
                        source="/shuttle/movie.mkv",
                        destination="/library/movie.mkv",
                        status=JournalStatus.COMPLETED,
                    )
                },
            )


            save_import_journal(
                journal,
                destination,
            )


            restored = load_import_journal(
                destination
            )


            passed = (
                restored is not None
                and restored.operation_id
                == "DF-VERIFY-001"
                and restored.completed == 1
            )


            detail = (
                "Atomic save and restore passed"
                if passed
                else "Restored journal did not match"
            )


    except Exception as exc:

        passed = False
        detail = str(exc)


    return VerificationCheck(
        name="Import journal",
        passed=passed,
        detail=detail,
    )


def _operation_check(
    manager: OperationManager,
) -> VerificationCheck:

    if not manager.active:

        return VerificationCheck(
            name="Active operation",
            passed=True,
            detail="No active operation",
        )


    try:

        operation = manager.require_operation()

        valid = manager.validate_snapshot()


        return VerificationCheck(
            name="Active operation",
            passed=valid,
            detail=(
                f"{operation.id} — "
                f"{manager.state.value} — "
                f"{'snapshot valid' if valid else 'snapshot invalid'}"
            ),
        )


    except Exception as exc:

        return VerificationCheck(
            name="Active operation",
            passed=False,
            detail=str(exc),
        )


def run_system_verification(
    *,
    config,
    operation_manager: OperationManager,
    temp_directory: Path,
) -> SystemVerificationResult:

    checks = []


    shuttle = Path(config.shuttle)


    checks.append(
        _path_exists_check(
            "Shuttle path",
            shuttle,
        )
    )


    for index, library in enumerate(
        config.movie_libraries,
        start=1,
    ):

        library = Path(library)


        checks.append(
            _path_exists_check(
                f"Movie library {index}",
                library,
            )
        )


        checks.append(
            _directory_writable_check(
                f"Movie library {index} writable",
                library,
            )
        )


    for index, library in enumerate(
        config.tv_libraries,
        start=1,
    ):

        library = Path(library)


        checks.append(
            _path_exists_check(
                f"TV library {index}",
                library,
            )
        )


        checks.append(
            _directory_writable_check(
                f"TV library {index} writable",
                library,
            )
        )


    checks.append(
        _directory_writable_check(
            "Report directory writable",
            Path(config.report_directory),
        )
    )


    checks.append(
        _directory_writable_check(
            "Temporary directory writable",
            Path(temp_directory),
        )
    )


    checks.append(
        VerificationCheck(
            name="Library Protection",
            passed=bool(config.read_only),
            detail=(
                "Enabled"
                if config.read_only
                else "Disabled"
            ),
        )
    )


    checks.extend(
        _ship_mode_checks(
            config
        )
    )


    checks.append(
        _snapshot_engine_check()
    )

    checks.append(
        _journal_engine_check()
    )

    checks.append(
        _operation_check(
            operation_manager
        )
    )


    return SystemVerificationResult(
        checks=checks
    )
