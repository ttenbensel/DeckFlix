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
)
from deckflix_app.importer import print_certificate
from deckflix_app.screens import (
    TerminalImportMonitor,
    show_import_preflight,
    show_operation_dashboard,
)

def begin_operation():
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
            shuttle_path=SHUTTLE,
            movie_libraries=config.movie_libraries,
            tv_libraries=config.tv_libraries,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print()
        print("Operation could not be created.")
        print(exc)
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


def operation_dashboard(operation_manager):
    show_operation_dashboard(operation_manager)


def clear_operation():
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
    delete_saved_operation(operation_state_path)
    print("Operation cleared.")


def approve_operation():
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

    ready = plan.count(ApprovalStatus.READY)

    print()
    print(f"Operation          {operation_manager.operation.id}")
    print(f"Ready imports      {ready}")
    print(f"Needs review       {plan.count(ApprovalStatus.REVIEW)}")
    print(f"Skipped            {plan.count(ApprovalStatus.SKIPPED)}")
    print()
    print("Only NEW media marked READY will be approved.")
    print("Upgrades and review items will not be approved.")

    answer = input(
        "Approve all READY imports? (y/N): "
    ).strip().lower()

    if answer != "y":
        print("Approval cancelled.")
        return

    try:
        approved = approve_ready_items(operation_manager)
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

    try:
        result = run_import_preflight(
            operation_manager,
            movie_library=movies,
            tv_library=tv,
            temp_dir=config.import_staging_directory,
        )
    except Exception as exc:
        print()
        print(
            f"Preflight could not run: {exc}"
        )
        return

    show_import_preflight(
        result,
        read_only=config.read_only,
    )


def enable_import_mode(
    operation_manager,
    operation_state_path,
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

    print()
    print(f"Operation           {operation.id}")
    print(
        f"Approved files      "
        f"{operation_manager.approval_plan.count(ApprovalStatus.APPROVED)}"
    )
    print()
    print("Library Protection will remain enabled globally.")
    print(
        "Only this approved operation will receive "
        "temporary write permission."
    )
    print()
    print("Import Mode will automatically switch off after:")
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
        print(f"Import Mode could not be enabled: {exc}")
        return

    save_operation_manager(
        operation_manager,
        operation_state_path,
    )

    print()
    print("Import Mode enabled for this operation.")
    print("Library Protection remains active for all other actions.")

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

    if (
        config.read_only
        and not operation_manager.import_authorized
    ):
        print()
        print("IMPORT BLOCKED")
        print("──────────────")
        print("Library Protection is enabled.")
        print("Enable Import Mode for this approved operation first.")
        print()
        print("No files have been copied, moved, or deleted.")
        return

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
            read_only=(
                config.read_only
                and (
                    not operation_manager.import_authorized
                )
            ),
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
        print("No completed library files will be recopied.")
        return

    except Exception as exc:
        print()
        print(f"Import failed: {exc}")

        if (
            operation_manager.state is not None
            and operation_manager.state.value == "IMPORTING"
        ):
            try:
                operation_manager.pause_import()
            except InvalidOperationTransition:
                pass

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
        print_certificate(certificate)

