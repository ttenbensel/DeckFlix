from collections import OrderedDict


class RepairQueue:
    """
    Session-only repair queue.

    Stores CleanupPlan objects only.
    Never performs filesystem changes.
    """

    def __init__(self):
        self._plans = OrderedDict()

    def add(self, plan):
        """
        Add or replace a cleanup plan.
        """

        self._plans[plan.release_key] = plan

    def remove(self, release_key):
        """
        Remove a cleanup plan.
        """

        self._plans.pop(release_key, None)

    def clear(self):
        """
        Remove every queued plan.
        """

        self._plans.clear()

    def plans(self):
        """
        Return queued plans.
        """

        return list(self._plans.values())

    @property
    def count(self):
        return len(self._plans)

    @property
    def recoverable_bytes(self):
        return sum(
            plan.recovered_bytes
            for plan in self._plans.values()
        )
