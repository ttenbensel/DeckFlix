from dataclasses import dataclass, field

from .models import ImportJob


@dataclass(slots=True)
class ImportFailure:
    job: ImportJob
    error: Exception

    @property
    def message(self) -> str:
        return str(self.error)


@dataclass(slots=True)
class ImportResult:
    total: int = 0
    completed: int = 0
    failed: int = 0
    failures: list[ImportFailure] = field(default_factory=list)

    @property
    def successful(self) -> bool:
        return self.total > 0 and self.failed == 0 and self.completed == self.total

    @property
    def safe_to_empty(self) -> bool:
        """
        This only confirms that all jobs processed by this import operation
        completed successfully.

        Later shuttle safety checks will also verify:
        - no pending queue entries
        - correct shuttle identity
        - correct destination identity
        - no temporary files left behind
        - destination files still exist
        """
        return self.successful
