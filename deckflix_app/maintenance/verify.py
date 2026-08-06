from dataclasses import dataclass
from pathlib import Path

from .checksum import file_checksum


@dataclass(slots=True)
class IntegrityResult:
    success: bool
    source_size: int | None
    destination_size: int | None
    source_checksum: str | None
    destination_checksum: str | None
    reason: str | None = None


def verify_integrity(
    source: Path,
    destination: Path,
) -> IntegrityResult:
    source = Path(source)
    destination = Path(destination)

    if not source.exists():
        return IntegrityResult(
            success=False,
            source_size=None,
            destination_size=None,
            source_checksum=None,
            destination_checksum=None,
            reason="Source file missing",
        )

    if not destination.exists():
        return IntegrityResult(
            success=False,
            source_size=source.stat().st_size,
            destination_size=None,
            source_checksum=file_checksum(source),
            destination_checksum=None,
            reason="Destination file missing",
        )

    source_size = source.stat().st_size
    destination_size = destination.stat().st_size

    source_hash = file_checksum(source)
    destination_hash = file_checksum(destination)

    if source_size != destination_size:
        return IntegrityResult(
            success=False,
            source_size=source_size,
            destination_size=destination_size,
            source_checksum=source_hash,
            destination_checksum=destination_hash,
            reason="File size mismatch",
        )

    if source_hash != destination_hash:
        return IntegrityResult(
            success=False,
            source_size=source_size,
            destination_size=destination_size,
            source_checksum=source_hash,
            destination_checksum=destination_hash,
            reason="Checksum mismatch",
        )

    return IntegrityResult(
        success=True,
        source_size=source_size,
        destination_size=destination_size,
        source_checksum=source_hash,
        destination_checksum=destination_hash,
    )
