from pathlib import Path

from deckflix_app.decision import ApprovalStatus
from deckflix_app.operation import (
    InvalidOperationTransition,
    approve_ready_items,
    delete_saved_operation,
    execute_operation,
    prepare_operation,
    run_import_preflight,
    save_operation_manager,
    reconcile_identical_files,
    preserve_unresolved_in_review_hold,
    validate_review_hold_evidence,
    validate_snapshot_evidence,
    create_final_safety_certificate,
    run_shuttle_action_preflight,
    execute_empty_and_unmount,
    execute_unmount_only,
)
from deckflix_app.importer import print_certificate
from deckflix_app.screens import (
    TerminalImportMonitor,
    show_import_preflight,
    show_operation_dashboard,
)


def begin_operation(
    operation_manager,
    shuttle,
    config,
    operation_state_path,
):
    print()
    print("Begin Shuttle Operation")
    print("═══════════════════════")

    if operation_manager.active:
        operation = operation_manager.require_operation()

        print()
        print("An operation is already active.")
        print(f"ID     {operation.id}")
        print(f"State  {operation.state.value}")
        print()
        print("Use Operation Dashboard to review it.")
        return

    print()
    print("Creating immutable shuttle snapshot...")
    print("Building decision queue...")
    print("Building approval plan...")

    try:
        operation = prepare_operation(
            operation_manager,
            shuttle_path=shuttle,
            movie_libraries=config.movie_libraries,
            tv_libraries=config.tv_libraries,
        )

    except (
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
    ) as exc:
        print()
        print("SHUTTLE OPERATION BLOCKED")
        print("─────────────────────────")
        print(exc)
        print()
        print(
            "No operation has been created and "
            "no files have been changed."
        )
        return

    except InvalidOperationTransition as exc:
        print()
        print("Operation state error.")
        print(exc)
        return

    print()
    print("Operation Ready")
    print("───────────────")
    print(f"ID                 {operation.id}")
    print(f"State              {operation.state.value}")
    print(
        f"Snapshot files     "
        f"{operation.snapshot.file_count}"
    )
    print(
        f"Decisions          "
        f"{operation_manager.decisions.total}"
    )

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    print()
    print("Nothing has been imported or changed.")


def verify_existing_library_copies(
    operation_manager,
    operation_state_path,
):
    import time

    print()
    print("Verify Existing Library Copies")
    print("══════════════════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    if operation_manager.decisions is None:
        print()
        print("No decision queue is available.")
        return

    existing_candidates = sum(
        1
        for item in operation_manager.decisions.items
        if item.existing is not None
    )

    print()
    print(
        f"Existing candidates  "
        f"{existing_candidates}"
    )
    print()
    print(
        "Equal file size will only select "
        "SHA-256 candidates."
    )
    print(
        "A file is marked IDENTICAL only after "
        "both files produce the same SHA-256."
    )
    print()
    print(
        "This may take a long time for a large "
        "shuttle."
    )

    answer = input(
        "Begin SHA-256 verification? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Verification cancelled.")
        return

    started = time.monotonic()
    last_current = 0

    def show_progress(progress):
        nonlocal last_current

        should_print = (
            progress.current == 1
            or progress.current == progress.total
            or progress.current - last_current >= 25
        )

        if not should_print:
            return

        last_current = progress.current

        elapsed_minutes = (
            time.monotonic() - started
        ) / 60

        verified_gb = (
            progress.verified_bytes
            / 1024**3
        )

        print(
            f"{progress.current}/"
            f"{progress.total}  "
            f"IDENTICAL={progress.identical:4}  "
            f"RESUMED={progress.resumed:4}  "
            f"HASHED={progress.hashed:4}  "
            f"DIFFERENT={progress.different:3}  "
            f"ERROR={progress.unavailable:3}  "
            f"Verified={verified_gb:.2f} GB  "
            f"Elapsed={elapsed_minutes:.1f}m"
        )

    print()
    print("SHA-256 Verification")
    print("────────────────────")

    try:
        result = reconcile_identical_files(
            operation_manager,
            progress=show_progress,
        )

    except KeyboardInterrupt:
        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print()
        print("VERIFICATION STOPPED")
        print("────────────────────")
        print(
            "Completed IDENTICAL results "
            "have been retained."
        )
        print(
            "The shuttle and libraries "
            "have not been modified."
        )
        return

    except InvalidOperationTransition as exc:
        print()
        print(
            f"Verification could not run: {exc}"
        )
        return

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    print()
    print("Reconciliation Result")
    print("═════════════════════")
    print(
        f"Existing candidates  "
        f"{result.candidates}"
    )
    print(
        f"Same-size candidates "
        f"{result.same_size}"
    )
    print(
        f"SHA-256 identical    "
        f"{result.identical}"
    )
    print(
        f"Resumed              "
        f"{result.resumed}"
    )
    print(
        f"Freshly hashed       "
        f"{result.hashed}"
    )
    print(
        f"Different            "
        f"{result.different}"
    )
    print(
        f"Unavailable/error    "
        f"{result.unavailable}"
    )
    print(
        f"Verified data        "
        f"{result.verified_bytes / 1024**3:.2f} GB"
    )
    print()
    print(
        "No shuttle or library files "
        "have been changed."
    )


def preserve_review_hold(
    operation_manager,
    operation_state_path,
    config,
):
    import time

    print()
    print("Preserve Unresolved in Review Hold")
    print("══════════════════════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    try:
        operation_manager.require_valid_snapshot()

    except Exception as exc:
        print()
        print("REVIEW HOLD BLOCKED")
        print("───────────────────")
        print(exc)
        print()
        print(
            "No shuttle or library files "
            "have been changed."
        )
        return

    try:
        validation = validate_review_hold_evidence(
            operation_manager
        )

    except Exception as exc:
        print()
        print(
            f"Existing Review Hold evidence "
            f"could not be validated: {exc}"
        )
        return

    if validation.checked:
        print()
        print("Existing Review Hold Evidence")
        print("─────────────────────────────")
        print(
            f"Checked             "
            f"{validation.checked}"
        )
        print(
            f"Valid               "
            f"{validation.valid}"
        )
        print(
            f"Invalidated         "
            f"{validation.invalid}"
        )

    ledger = operation_manager.require_ledger()

    unresolved_entries = [
        entry
        for entry in ledger.entries.values()
        if entry.disposition.value == "UNRESOLVED"
    ]

    unresolved_files = len(
        unresolved_entries
    )

    snapshot_map = {
        item.relative_path: item
        for item
        in operation_manager
        .require_operation()
        .snapshot
        .files
    }

    unresolved_bytes = sum(
        snapshot_map[
            entry.relative_path
        ].size
        for entry in unresolved_entries
        if entry.relative_path
        in snapshot_map
    )

    print()
    print("Review Hold Plan")
    print("────────────────")
    print(
        f"Unresolved files    "
        f"{unresolved_files}"
    )
    print(
        f"Data                "
        f"{unresolved_bytes / 1024**3:.2f} GB"
    )
    print(
        f"Destination         "
        f"{config.review_hold_directory}"
    )

    if unresolved_files == 0:
        print()
        print(
            "No unresolved shuttle files remain."
        )
        return

    print()
    print(
        "Each unresolved file will be copied "
        "to an operation-specific Review Hold "
        "and SHA-256 verified."
    )
    print(
        "The shuttle source will NOT be "
        "moved or deleted."
    )

    answer = input(
        "Preserve all unresolved files? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Review Hold cancelled.")
        return

    started = time.monotonic()
    last_current = 0

    def show_progress(progress):
        nonlocal last_current

        should_print = (
            progress.current == 1
            or progress.current == progress.total
            or progress.current - last_current >= 10
        )

        if not should_print:
            return

        last_current = progress.current

        elapsed_minutes = (
            time.monotonic()
            - started
        ) / 60

        verified_gb = (
            progress.verified_bytes
            / 1024**3
        )

        print(
            f"{progress.current}/"
            f"{progress.total}  "
            f"VERIFIED={progress.completed:4}  "
            f"RESUMED={progress.resumed:4}  "
            f"FAILED={progress.failed:3}  "
            f"Verified={verified_gb:.2f} GB  "
            f"Elapsed={elapsed_minutes:.1f}m"
        )

    print()
    print("Review Hold Preservation")
    print("────────────────────────")

    try:
        result = preserve_unresolved_in_review_hold(
            operation_manager,
            review_hold_directory=(
                config.review_hold_directory
            ),
            progress=show_progress,
        )

    except KeyboardInterrupt:
        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print()
        print("REVIEW HOLD STOPPED")
        print("───────────────────")
        print(
            "Completed verified Review Hold "
            "entries have been retained."
        )
        print(
            "No shuttle files have been deleted."
        )
        return

    except Exception as exc:
        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print(
            f"Review Hold failed: {exc}"
        )
        print(
            "No shuttle files have been deleted."
        )
        return

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    ledger = operation_manager.require_ledger()

    print()
    print("Review Hold Result")
    print("══════════════════")
    print(
        f"Selected            "
        f"{result.total}"
    )
    print(
        f"Verified            "
        f"{result.completed}"
    )
    print(
        f"Resumed             "
        f"{result.resumed}"
    )
    print(
        f"Failed              "
        f"{result.failed}"
    )
    print(
        f"Verified data       "
        f"{result.verified_bytes / 1024**3:.2f} GB"
    )
    print()
    print("Snapshot Accounting")
    print("───────────────────")
    print(
        f"Accounted           "
        f"{ledger.accounted_files}"
    )
    print(
        f"Unresolved          "
        f"{ledger.unresolved_files}"
    )
    print(
        f"Coverage            "
        f"{ledger.coverage_percent}%"
    )

    if result.failed:
        print()
        print("Failures")
        print("────────")

        for failure in result.failures[:10]:
            print(
                f"- {failure.source}: "
                f"{failure.error}"
            )

        if len(result.failures) > 10:
            print(
                f"... {len(result.failures) - 10} "
                "more failure(s)"
            )

    print()
    print(
        "No shuttle files have been "
        "moved or deleted."
    )


def final_snapshot_safety_validation(
    operation_manager,
    operation_state_path,
):
    import time

    print()
    print("Final Snapshot Safety Validation")
    print("════════════════════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    try:
        operation_manager.require_valid_snapshot()

    except Exception as exc:
        print()
        print("FINAL SAFETY GATE BLOCKED")
        print("─────────────────────────")
        print(exc)
        print()
        print("Status             NOT SAFE TO EMPTY")
        return

    ledger = operation_manager.require_ledger()

    print()
    print("Snapshot Accounting")
    print("───────────────────")
    print(
        f"Files              "
        f"{ledger.total_files}"
    )
    print(
        f"Accounted          "
        f"{ledger.accounted_files}"
    )
    print(
        f"Unresolved         "
        f"{ledger.unresolved_files}"
    )
    print(
        f"Coverage           "
        f"{ledger.coverage_percent}%"
    )

    if not ledger.coverage_complete:
        print()
        print("FINAL SAFETY GATE BLOCKED")
        print("─────────────────────────")
        print(
            "Snapshot accounting is not complete."
        )
        print()
        print("Status             NOT SAFE TO EMPTY")
        return

    print()
    print(
        "DeckFlix will now revalidate every "
        "accounted evidence file."
    )
    print(
        "IMPORTED, IDENTICAL, and REVIEW_HOLD "
        "evidence will be SHA-256 checked."
    )
    print()
    print(
        "No files will be copied, moved, "
        "changed, or deleted."
    )

    answer = input(
        "Run final evidence validation? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Final validation cancelled.")
        return

    print()
    print("Evidence Validation")
    print("───────────────────")

    # A fresh validation attempt withdraws any
    # previous final safety certificate.
    operation_manager.final_safety_certificate = None

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    started = time.monotonic()

    try:
        result = validate_snapshot_evidence(
            operation_manager
        )

    except KeyboardInterrupt:
        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print()
        print("VALIDATION STOPPED")
        print("──────────────────")
        print(
            "Any evidence already proven invalid "
            "has been demoted to UNRESOLVED."
        )
        print("Status             NOT SAFE TO EMPTY")
        return

    except Exception as exc:
        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print("FINAL SAFETY GATE BLOCKED")
        print("─────────────────────────")
        print(exc)
        print()
        print("Status             NOT SAFE TO EMPTY")
        return

    if result.safe:
        create_final_safety_certificate(
            operation_manager,
            result,
        )

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    elapsed_minutes = (
        time.monotonic()
        - started
    ) / 60

    print()
    print("Final Evidence Audit")
    print("════════════════════")
    print(
        f"Snapshot files     "
        f"{result.total}"
    )
    print(
        f"Valid evidence     "
        f"{result.valid}"
    )
    print(
        f"Invalid evidence   "
        f"{result.invalid}"
    )
    print(
        f"Unresolved         "
        f"{result.unresolved}"
    )
    print()
    print("Disposition")
    print("───────────")
    print(
        f"Imported           "
        f"{result.imported}"
    )
    print(
        f"Identical          "
        f"{result.identical}"
    )
    print(
        f"Review Hold        "
        f"{result.review_hold}"
    )
    print()
    print(
        f"Verified data      "
        f"{result.verified_bytes / 1024**3:.2f} GB"
    )
    print(
        f"Evidence coverage  "
        f"{result.coverage_percent}%"
    )
    print(
        f"Elapsed            "
        f"{elapsed_minutes:.1f}m"
    )

    print()
    print("Status")
    print("──────")

    if result.safe:
        print("SAFE TO EMPTY")
        print()

        certificate = (
            operation_manager
            .final_safety_certificate
        )

        print(
            "Every shuttle snapshot file has "
            "current SHA-256 verified evidence."
        )

        if certificate is not None:
            print()
            print("Final Safety Certificate")
            print("────────────────────────")
            print(
                f"Validated          "
                f"{certificate.validated_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(
                f"Snapshot           "
                f"{certificate.snapshot_fingerprint[:16]}..."
            )
            print(
                f"Evidence           "
                f"{certificate.evidence_fingerprint[:16]}..."
            )
    else:
        print("NOT SAFE TO EMPTY")
        print()
        print(
            "One or more snapshot files lack "
            "valid current evidence."
        )

    print()
    print(
        "No shuttle or evidence files "
        "have been changed."
    )


def operation_dashboard(operation_manager):
    show_operation_dashboard(
        operation_manager
    )


def clear_operation(
    operation_manager,
    operation_state_path,
):
    print()
    print("Clear Current Operation")
    print("═══════════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    operation = operation_manager.require_operation()

    print()
    print(f"Operation  {operation.id}")
    print(f"State      {operation.state.value}")
    print()

    answer = input(
        "Discard this in-memory operation? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Operation retained.")
        return

    operation_manager.clear()
    delete_saved_operation(
        operation_state_path
    )

    print("Operation cleared.")


def approve_operation(
    operation_manager,
    operation_state_path,
):
    print()
    print("Approve Ready Imports")
    print("═════════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    plan = operation_manager.approval_plan

    if plan is None:
        print()
        print("No approval plan is available.")
        return

    ready = plan.count(
        ApprovalStatus.READY
    )

    print()
    print(
        f"Operation          "
        f"{operation_manager.operation.id}"
    )
    print(f"Ready imports      {ready}")
    print(
        f"Needs review       "
        f"{plan.count(ApprovalStatus.REVIEW)}"
    )
    print(
        f"Skipped            "
        f"{plan.count(ApprovalStatus.SKIPPED)}"
    )
    print()
    print(
        "Only NEW media marked READY "
        "will be approved."
    )
    print(
        "Upgrades and review items "
        "will not be approved."
    )

    answer = input(
        "Approve all READY imports? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Approval cancelled.")
        return

    try:
        approved = approve_ready_items(
            operation_manager
        )

    except InvalidOperationTransition as exc:
        print()
        print(f"Approval failed: {exc}")
        return

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    print()
    print(f"Approved {approved} import(s).")
    print("No files have been copied.")


def _run_final_import_gate(
    operation_manager,
    movies,
    tv,
    config,
):
    try:
        result = run_import_preflight(
            operation_manager,
            movie_library=movies,
            tv_library=tv,
            temp_dir=config.import_staging_directory,
            journal_path=(
                config.report_directory
                / "current-import-journal.json"
            ),
        )

    except Exception as exc:
        print()
        print("FINAL IMPORT GATE BLOCKED")
        print("─────────────────────────")
        print(
            f"Preflight could not run: {exc}"
        )
        print()
        print(
            "No files have been copied, moved, "
            "or deleted."
        )
        return None

    show_import_preflight(
        result,
        read_only=config.read_only,
    )

    if not result.ready:
        print()
        print("FINAL IMPORT GATE BLOCKED")
        print("─────────────────────────")
        print(
            "Import Mode cannot proceed until "
            "all preflight checks pass."
        )
        print()
        print(
            "No files have been copied, moved, "
            "or deleted."
        )
        return None

    return result


def full_import_preflight(
    operation_manager,
    movies,
    tv,
    config,
):
    print()
    print("Preparing full import preflight...")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    _run_final_import_gate(
        operation_manager,
        movies,
        tv,
        config,
    )


def enable_import_mode(
    operation_manager,
    operation_state_path,
    movies,
    tv,
    config,
):
    print()
    print("Enable Import Mode")
    print("══════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    operation = operation_manager.require_operation()

    if operation.state.value != "APPROVED":
        print()
        print(
            "The operation must be APPROVED before "
            "Import Mode can be enabled."
        )
        return

    if operation_manager.import_authorized:
        print()
        print("Import Mode is already enabled.")
        return

    plan = operation_manager.approval_plan

    if plan is None:
        print()
        print("No approval plan is attached.")
        return

    approved = plan.count(
        ApprovalStatus.APPROVED
    )

    if approved <= 0:
        print()
        print("IMPORT BLOCKED")
        print("──────────────")
        print("No approved files are available.")
        return

    print()
    print("Running final import gate...")

    result = _run_final_import_gate(
        operation_manager,
        movies,
        tv,
        config,
    )

    if result is None:
        return

    print()
    print("Final Import Gate")
    print("─────────────────")
    print(f"Operation           {operation.id}")
    print("Operation State     PASS")
    print("Snapshot            PASS")
    print(
        f"Approved files      "
        f"{result.approved_files}"
    )
    print(
        f"Review excluded     "
        f"{result.review_items}"
    )
    print("Sources             PASS")
    print("Destinations        PASS")
    print("Storage             PASS")
    print("Write access        PASS")
    print()
    print("RESULT              READY FOR IMPORT")

    print()
    print(
        "Library Protection will remain "
        "enabled globally."
    )
    print(
        "Only this approved operation will "
        "receive temporary write permission."
    )
    print()
    print(
        "Import Mode will automatically "
        "switch off after:"
    )
    print("- successful completion")
    print("- Ctrl+C pause")
    print("- an import failure")
    print("- clearing the operation")
    print()

    answer = input(
        "Enable Import Mode for this operation? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Import Mode remains disabled.")
        return

    try:
        operation_manager.authorize_import()

    except InvalidOperationTransition as exc:
        print()
        print(
            f"Import Mode could not be enabled: "
            f"{exc}"
        )
        return

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    print()
    print(
        "Import Mode enabled for this operation."
    )
    print(
        "Library Protection remains active "
        "for all other actions."
    )


def execute_current_operation(
    operation_manager,
    movies,
    tv,
    config,
    operation_state_path,
):
    print()
    print("Execute Operation")
    print("═════════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        return

    if not operation_manager.import_authorized:
        print()
        print("IMPORT BLOCKED")
        print("──────────────")
        print("Import Mode is not enabled.")
        print(
            "Enable Import Mode for this "
            "approved operation first."
        )
        print()
        print(
            "No files have been copied, moved, "
            "or deleted."
        )
        return

    print()
    print(
        "Re-validating final import gate "
        "immediately before execution..."
    )

    result = _run_final_import_gate(
        operation_manager,
        movies,
        tv,
        config,
    )

    if result is None:
        operation_manager.revoke_import_authorization()

        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print(
            "Import Mode has been automatically "
            "disabled."
        )
        return

    print()
    print("FINAL IMPORT GATE PASSED")
    print("────────────────────────")
    print(
        f"Approved files      "
        f"{result.approved_files}"
    )
    print(
        f"Review excluded     "
        f"{result.review_items}"
    )
    print()

    answer = input(
        "Execute all approved imports? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Import cancelled.")
        return

    monitor = TerminalImportMonitor(
        operation_id=operation_manager.operation.id
    )

    try:
        certificate = execute_operation(
            operation_manager,
            movie_library=movies,
            tv_library=tv,
            temp_dir=config.import_staging_directory,
            read_only=False,
            progress=monitor,
            history_directory=(
                config.report_directory
                / "operations"
            ),
            journal_path=(
                config.report_directory
                / "current-import-journal.json"
            ),
        )

    except KeyboardInterrupt:
        print()
        print()
        print("IMPORT PAUSED")
        print("─────────────")
        print(
            "The current file will be reconciled "
            "when the import resumes."
        )

        try:
            operation_manager.pause_import()
        except InvalidOperationTransition:
            pass

        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print("Operation state and journal saved.")
        print(
            "No completed library files will "
            "be recopied."
        )
        return

    except Exception as exc:
        print()
        print(f"Import failed: {exc}")

        if (
            operation_manager.state is not None
            and operation_manager.state.value
            == "IMPORTING"
        ):
            try:
                operation_manager.pause_import()
            except InvalidOperationTransition:
                pass

        operation_manager.revoke_import_authorization()

        save_operation_manager(
            operation_manager,
            operation_state_path,
        )
        return

    if certificate is not None:
        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print_certificate(
            certificate
        )


def empty_and_eject_preflight(
    operation_manager,
    operation_state_path,
):
    print()
    print("Empty & Eject")
    print("═════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        print()
        print("Status              BLOCKED")
        print(
            "Actual Empty & Eject is not enabled."
        )
        return

    operation = (
        operation_manager.require_operation()
    )

    print()
    print(f"Operation           {operation.id}")
    print(
        f"Shuttle             "
        f"{operation.snapshot.shuttle_path}"
    )
    print(
        f"Snapshot files      "
        f"{operation.snapshot.file_count}"
    )

    print()
    print(
        "Running final safety preflight..."
    )
    print(
        "This may take time because current "
        "evidence is SHA-256 verified."
    )

    try:
        result = run_shuttle_action_preflight(
            operation_manager
        )

    except KeyboardInterrupt:
        operation_manager.final_safety_certificate = None

        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print()
        print("PREFLIGHT STOPPED")
        print("─────────────────")
        print("Status              BLOCKED")
        print(
            "Final Safety Certificate withdrawn."
        )
        print()
        print("No files have been changed.")
        return

    except Exception as exc:
        operation_manager.final_safety_certificate = None

        save_operation_manager(
            operation_manager,
            operation_state_path,
        )

        print()
        print("PREFLIGHT FAILED")
        print("────────────────")
        print(exc)
        print()
        print("Status              BLOCKED")
        print()
        print("No files have been changed.")
        return

    # The preflight can refresh or withdraw the
    # certificate, so always persist the result.
    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    print()
    print("Final Safety Preflight")
    print("──────────────────────")
    print(
        f"Snapshot files      "
        f"{result.snapshot_files}"
    )
    print(
        f"Evidence verified   "
        f"{result.validated_files}"
    )
    print(
        f"Unresolved          "
        f"{result.unresolved}"
    )
    print(
        f"Verified data       "
        f"{result.verified_bytes / 1024**3:.2f} GB"
    )

    certificate = (
        operation_manager
        .final_safety_certificate
    )

    print()
    print("Safety Gate")
    print("───────────")

    if result.ready:
        print("Certificate         VALID")
        print("Snapshot            VALID")
        print("Evidence            VERIFIED")
        print(
            f"Coverage            "
            f"{result.validated_files} / "
            f"{result.snapshot_files}"
        )
        print("Status              READY")

        if certificate is not None:
            print()
            print(
                f"Validated           "
                f"{certificate.validated_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

    else:
        print(
            "Certificate         "
            f"{'VALID' if certificate is not None else 'INVALID'}"
        )
        print("Status              BLOCKED")

        if result.reasons:
            print()
            print("Blocking Reasons")
            print("────────────────")

            for reason in result.reasons:
                print(f"- {reason}")

    print()
    print("No files have been changed.")
    print()
    print(
        "Actual Empty & Eject is not enabled yet."
    )


def handle_shuttle_operation_choice(
    choice,
    *,
    operation_manager,
    shuttle,
    config,
    operation_state_path,
):
    """
    Route one Shuttle Operation menu selection.

    Return False only when the caller should leave
    the Shuttle Operation menu.
    """
    if choice == "1":
        begin_operation(
            operation_manager=operation_manager,
            shuttle=shuttle,
            config=config,
            operation_state_path=operation_state_path,
        )

    elif choice == "2":
        verify_existing_library_copies(
            operation_manager=operation_manager,
            operation_state_path=operation_state_path,
        )

    elif choice == "3":
        preserve_review_hold(
            operation_manager=operation_manager,
            operation_state_path=operation_state_path,
            config=config,
        )

    elif choice == "4":
        final_snapshot_safety_validation(
            operation_manager=operation_manager,
            operation_state_path=operation_state_path,
        )

    elif choice == "5":
        shuttle_release(
            operation_manager=operation_manager,
            operation_state_path=operation_state_path,
        )

    elif choice == "6":
        operation_dashboard(
            operation_manager
        )

    elif choice == "7":
        clear_operation(
            operation_manager=operation_manager,
            operation_state_path=operation_state_path,
        )

    elif choice == "8":
        return False

    else:
        print("Invalid option.")

    return True


def shuttle_release(
    operation_manager,
    operation_state_path,
):
    print()
    print("Shuttle Release")
    print("═══════════════")

    if not operation_manager.active:
        print()
        print("No operation is active.")
        print("Nothing has been changed.")
        return

    operation = (
        operation_manager.require_operation()
    )

    print()
    print(f"Operation    {operation.id}")
    print(
        f"Shuttle      "
        f"{operation.snapshot.shuttle_path}"
    )

    print()
    print("1. Empty & Eject")
    print("2. Eject Only")
    print("3. Cancel")
    print()

    choice = input(
        "Select option: "
    ).strip()

    if choice == "1":
        print()
        print("EMPTY & EJECT")
        print("═════════════")
        print()
        print("WARNING — DESTRUCTIVE ACTION")
        print()
        print(
            "This will permanently remove ALL files "
            "from the mounted SHUTTLE."
        )
        print(
            "Library and Review Hold files are "
            "not affected."
        )
        print()
        print(
            "A fresh SHA-256 safety preflight will "
            "run before deletion is permitted."
        )
        print()
        print(
            "To continue, type the operation ID "
            "exactly:"
        )
        print(operation.id)
        print()

        confirmation = input(
            "Operation ID: "
        ).strip()

        if confirmation != operation.id:
            print()
            print("CANCELLED")
            print("No files have been changed.")
            return

        print()
        print(
            "Running final safety checks..."
        )

        try:
            result = execute_empty_and_unmount(
                operation_manager,
                confirmation=confirmation,
            )

        except KeyboardInterrupt:
            print()
            print()
            print("EMPTY & EJECT INTERRUPTED")
            print(
                "Check shuttle status before "
                "continuing."
            )
            return

        except Exception as exc:
            print()
            print("EMPTY & EJECT BLOCKED")
            print("─────────────────────")
            print(exc)
            print()
            print(
                "DeckFlix has not declared the "
                "shuttle safely released."
            )
            return

        if not (
            result.emptied
            and result.unmounted
        ):
            print()
            print("RELEASE VERIFICATION FAILED")
            print(
                "DeckFlix will retain the active "
                "operation."
            )
            return

        operation_manager.clear()

        delete_saved_operation(
            operation_state_path
        )

        print()
        print("Shuttle Released")
        print("════════════════")
        print("Contents       EMPTY")
        print("Filesystem     UNMOUNTED")
        print(
            f"Device         {result.source}"
        )
        print(
            f"Filesystem     {result.filesystem}"
        )
        print(
            f"Label          {result.label}"
        )
        print()
        print(
            "The shuttle may now be safely "
            "disconnected."
        )
        return

    if choice == "2":
        print()
        print("Eject Only")
        print("══════════")
        print()
        print(
            "No files will be deleted from "
            "the shuttle."
        )
        print()

        confirmation = input(
            "Unmount SHUTTLE now? (y/N): "
        ).strip().lower()

        if confirmation != "y":
            print()
            print("CANCELLED")
            print("No files have been changed.")
            return

        try:
            result = execute_unmount_only(
                operation_manager
            )

        except KeyboardInterrupt:
            print()
            print()
            print("EJECT INTERRUPTED")
            print(
                "Check shuttle status before "
                "continuing."
            )
            return

        except Exception as exc:
            print()
            print("EJECT BLOCKED")
            print("─────────────")
            print(exc)
            print()
            print(
                "No shuttle files were intentionally "
                "deleted."
            )
            return

        if not result.unmounted:
            print()
            print("EJECT VERIFICATION FAILED")
            print(
                "DeckFlix will retain the active "
                "operation."
            )
            return

        operation_manager.clear()

        delete_saved_operation(
            operation_state_path
        )

        print()
        print("Shuttle Released")
        print("════════════════")
        print("Contents       PRESERVED")
        print("Filesystem     UNMOUNTED")
        print(
            f"Device         {result.source}"
        )
        print()
        print(
            "The shuttle may now be safely "
            "disconnected."
        )
        return

    if choice == "3":
        print()
        print("Cancelled.")
        return

    print()
    print("Invalid option.")
