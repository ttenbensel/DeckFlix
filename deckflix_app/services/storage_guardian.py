from dataclasses import dataclass


@dataclass(slots=True)
class StorageAssessment:
    required_bytes: int
    available_bytes: int
    repair_recovery_bytes: int = 0
    quarantine_recovery_bytes: int = 0

    @property
    def shortfall_bytes(self):
        return max(
            0,
            self.required_bytes - self.available_bytes,
        )

    @property
    def potential_recovery_bytes(self):
        return (
            self.repair_recovery_bytes
            + self.quarantine_recovery_bytes
        )

    @property
    def can_import_now(self):
        return self.shortfall_bytes == 0

    @property
    def can_import_after_review(self):
        return (
            self.shortfall_bytes > 0
            and self.potential_recovery_bytes >= self.shortfall_bytes
        )


def assess_storage(
    required_bytes,
    available_bytes,
    repair_recovery_bytes=0,
    quarantine_recovery_bytes=0,
):
    """
    Build a read-only storage assessment.

    Nothing is deleted, moved, or changed.
    """

    return StorageAssessment(
        required_bytes=required_bytes,
        available_bytes=available_bytes,
        repair_recovery_bytes=repair_recovery_bytes,
        quarantine_recovery_bytes=quarantine_recovery_bytes,
    )


def bytes_to_gb(value):
    return value / 1024**3


def show_storage_assessment(assessment):
    print()
    print("Storage Guardian")
    print("════════════════")

    print()
    print(f"Required            {bytes_to_gb(assessment.required_bytes):.2f} GB")
    print(f"Available           {bytes_to_gb(assessment.available_bytes):.2f} GB")
    print(f"Shortfall           {bytes_to_gb(assessment.shortfall_bytes):.2f} GB")

    print()
    print("Potential Recovery")
    print("──────────────────")
    print(
        f"Repair Queue        "
        f"{bytes_to_gb(assessment.repair_recovery_bytes):.2f} GB"
    )
    print(
        f"Quarantine Review   "
        f"{bytes_to_gb(assessment.quarantine_recovery_bytes):.2f} GB"
    )
    print(
        f"Total               "
        f"{bytes_to_gb(assessment.potential_recovery_bytes):.2f} GB"
    )

    print()
    print("Status")
    print("──────")

    if assessment.can_import_now:
        print("✓ Import can proceed now")
    elif assessment.can_import_after_review:
        print("⚠ Storage review can recover enough space")
    else:
        print("✗ Additional storage or library review required")

    print()
    print("Assessment only. Nothing has been changed.")
