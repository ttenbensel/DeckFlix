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
