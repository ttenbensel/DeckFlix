from dataclasses import dataclass


@dataclass(slots=True)
class StorageDevice:
    name: str
    capacity_tb: float
    role: str
    connection: str
    protected: bool


@dataclass(slots=True)
class StoragePlan:
    devices: list[StorageDevice]
    total_tb: float
    protected_tb: float

    @property
    def protection_percent(self) -> int:
        if self.total_tb == 0:
            return 0
        return round((self.protected_tb / self.total_tb) * 100)


def recommend(plan: StoragePlan) -> str:
    if plan.protection_percent < 50:
        return "Add a backup drive."

    if plan.protection_percent < 100:
        return "Increase backup coverage."

    return "Storage protection is excellent."
