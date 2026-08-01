from dataclasses import dataclass

from deckflix_app.importer import (
    ImportProgress,
    ImportStage,
)


@dataclass(slots=True)
class TerminalImportMonitor:
    last_percent: int = -1

    def __call__(
        self,
        event: ImportProgress,
    ) -> None:
        if event.stage is ImportStage.STARTING:
            print()
            print("Executing Operation")
            print("═══════════════════")
            print(f"Files approved     {event.total}")
            print()
            return

        if event.stage is ImportStage.FINISHED:
            print()
            print("Import Execution Complete")
            print("─────────────────────────")
            print(event.message)
            return

        source_name = (
            event.source.name
            if event.source is not None
            else ""
        )

        progress_bar = self._progress_bar(
            event.percent
        )

        print(
            f"\r{progress_bar} "
            f"{event.percent:3d}% "
            f"{event.current}/{event.total} "
            f"{event.stage.value:<10} "
            f"{source_name[:45]:<45}",
            end="",
            flush=True,
        )

        if event.stage in {
            ImportStage.COMPLETED,
            ImportStage.FAILED,
        }:
            print()

    @staticmethod
    def _progress_bar(
        percent: int,
        *,
        width: int = 24,
    ) -> str:
        complete = int(
            width * percent / 100
        )

        return (
            "["
            + "#" * complete
            + "-" * (width - complete)
            + "]"
        )
