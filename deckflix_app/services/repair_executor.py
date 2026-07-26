from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RepairExecutionPreview:
    """
    Read-only preview of queued repair actions.
    """

    moves: list[tuple[Path, Path]] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def move_count(self):
        return len(self.moves)

    @property
    def skipped_count(self):
        return len(self.skipped)


def build_execution_preview(plans, quarantine_root):
    """
    Build a dry-run preview from CleanupPlan objects.

    No directories are created and no files are moved.
    """

    quarantine_root = Path(quarantine_root)
    preview = RepairExecutionPreview()

    for plan in plans:
        title, year, _ = plan.release_key
        release_folder = (
            f"{title.title()} ({year})"
            if year
            else title.title()
        )

        for item in plan.quarantine:
            source = Path(item.path)

            if not source.exists():
                preview.skipped.append(
                    (source, "Source file no longer exists")
                )
                continue

            destination = (
                quarantine_root
                / release_folder
                / source.name
            )

            preview.moves.append(
                (source, destination)
            )

    return preview


def show_execution_preview(preview):
    """
    Display a dry-run repair preview.
    """

    print()
    print("Execute Repair — Dry Run")
    print("════════════════════════")

    print()
    print(f"Files proposed       {preview.move_count}")
    print(f"Files skipped        {preview.skipped_count}")

    if preview.moves:
        print()
        print("PROPOSED MOVES")
        print("──────────────")

        for source, destination in preview.moves:
            print()
            print(f"FROM  {source}")
            print(f"TO    {destination}")

    if preview.skipped:
        print()
        print("SKIPPED")
        print("───────")

        for source, reason in preview.skipped:
            print(f"{source}")
            print(f"  {reason}")

    print()
    print("Dry run only. Nothing has been moved.")
@dataclass(slots=True)
class RepairExecutionResult:
    """
    Result of executing an approved repair preview.
    """

    moved: list[tuple[Path, Path]] = field(default_factory=list)
    failed: list[tuple[Path, Path, str]] = field(default_factory=list)

    @property
    def moved_count(self):
        return len(self.moved)

    @property
    def failed_count(self):
        return len(self.failed)

    @property
    def success(self):
        return self.failed_count == 0


def execute_preview(preview):
    """
    Execute an already-reviewed RepairExecutionPreview.

    Files are moved to quarantine only.
    Existing destinations are never overwritten.
    Nothing is deleted.
    """

    result = RepairExecutionResult()

    for source, destination in preview.moves:
        if not source.exists():
            result.failed.append(
                (source, destination, "Source file no longer exists")
            )
            continue

        if destination.exists():
            result.failed.append(
                (source, destination, "Destination already exists")
            )
            continue

        try:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            source.rename(destination)

            result.moved.append(
                (source, destination)
            )

        except OSError as error:
            result.failed.append(
                (source, destination, str(error))
            )

    return result


def show_execution_result(result):
    """
    Display the result of a repair execution.
    """

    print()
    print("Repair Execution Result")
    print("═══════════════════════")

    print()
    print(f"Files moved          {result.moved_count}")
    print(f"Files failed         {result.failed_count}")

    if result.moved:
        print()
        print("MOVED TO QUARANTINE")
        print("───────────────────")

        for source, destination in result.moved:
            print()
            print(f"FROM  {source}")
            print(f"TO    {destination}")

    if result.failed:
        print()
        print("FAILED")
        print("──────")

        for source, destination, reason in result.failed:
            print()
            print(f"FROM  {source}")
            print(f"TO    {destination}")
            print(f"WHY   {reason}")

    print()
    print("Nothing has been deleted.")
def confirm_execution(preview):
    """
    Ask the user to explicitly approve execution.

    Returns True only when the user types EXECUTE.
    """

    print()
    print("Execute Approved Repairs")
    print("════════════════════════")

    print()
    print(f"Files to move      {preview.move_count}")
    print(f"Files skipped      {preview.skipped_count}")

    print()
    print("Safety")
    print("──────")
    print("• Files will be MOVED to quarantine")
    print("• Existing quarantine files are never overwritten")
    print("• Nothing will be deleted")

    print()
    confirm = input(
        "Type EXECUTE to continue: "
    ).strip()

    return confirm == "EXECUTE"
