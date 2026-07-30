"""Central policy decisions for DeckFlix operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from deckflix_app.config import DeckFlixConfig


class Operation(str, Enum):
    """Operations that may be permitted, limited, or blocked."""

    SCAN_LOCAL = "scan_local"
    IMPORT_MEDIA = "import_media"
    REPAIR_MEDIA = "repair_media"
    RESTORE_MEDIA = "restore_media"
    DELETE_MEDIA = "delete_media"

    USE_NETWORK = "use_network"
    DOWNLOAD_MEDIA = "download_media"
    DOWNLOAD_METADATA = "download_metadata"
    REFRESH_JELLYFIN = "refresh_jellyfin"
    CONTACT_EXTERNAL_SERVICE = "contact_external_service"


@dataclass(frozen=True)
class PolicyDecision:
    """An explainable decision returned by the policy engine."""

    allowed: bool
    operation: Operation
    reason: str
    approval_required: bool = False
    vpn_required: bool = False
    limited: bool = False

    def require(self) -> None:
        """Raise an error when the operation is not allowed."""

        if not self.allowed:
            raise PolicyDeniedError(self)


class PolicyDeniedError(RuntimeError):
    """Raised when an operation is blocked by policy."""

    def __init__(self, decision: PolicyDecision) -> None:
        self.decision = decision
        super().__init__(
            f"Operation '{decision.operation.value}' denied: "
            f"{decision.reason}"
        )


class PolicyEngine:
    """Translate DeckFlix configuration into operational permissions."""

    def __init__(self, config: DeckFlixConfig) -> None:
        self.config = config

    @property
    def profile(self) -> str:
        return self.config.operating_profile

    @property
    def low_impact(self) -> bool:
        return self.config.low_impact

    def decide(self, operation: Operation) -> PolicyDecision:
        """Return the policy decision for an operation."""

        local_operations = {
            Operation.SCAN_LOCAL,
            Operation.IMPORT_MEDIA,
            Operation.REPAIR_MEDIA,
            Operation.RESTORE_MEDIA,
        }

        network_operations = {
            Operation.USE_NETWORK,
            Operation.DOWNLOAD_MEDIA,
            Operation.DOWNLOAD_METADATA,
            Operation.REFRESH_JELLYFIN,
            Operation.CONTACT_EXTERNAL_SERVICE,
        }

        if operation in local_operations:
            return self._decide_local_operation(operation)

        if operation == Operation.DELETE_MEDIA:
            return self._decide_delete()

        if operation in network_operations:
            return self._decide_network_operation(operation)

        return PolicyDecision(
            allowed=False,
            operation=operation,
            reason="No policy rule exists for this operation.",
        )

    def _decide_local_operation(
        self,
        operation: Operation,
    ) -> PolicyDecision:
        if self.config.read_only and operation != Operation.SCAN_LOCAL:
            return PolicyDecision(
                allowed=False,
                operation=operation,
                reason="DeckFlix is running in read-only mode.",
            )

        approval_required = operation in {
            Operation.IMPORT_MEDIA,
            Operation.REPAIR_MEDIA,
            Operation.RESTORE_MEDIA,
        }

        if self.low_impact:
            reason = (
                "Local operation is permitted with Low Impact resource "
                "restrictions."
            )
        else:
            reason = "Local operation is permitted by the active profile."

        return PolicyDecision(
            allowed=True,
            operation=operation,
            reason=reason,
            approval_required=approval_required,
            limited=self.low_impact,
        )

    def _decide_delete(self) -> PolicyDecision:
        if self.config.read_only:
            return PolicyDecision(
                allowed=False,
                operation=Operation.DELETE_MEDIA,
                reason="Deletion is blocked because DeckFlix is read-only.",
            )

        return PolicyDecision(
            allowed=True,
            operation=Operation.DELETE_MEDIA,
            reason=(
                "Deletion is permitted only after explicit operator "
                "confirmation."
            ),
            approval_required=True,
        )

    def _decide_network_operation(
        self,
        operation: Operation,
    ) -> PolicyDecision:
        if self.profile == "ship_offline":
            return PolicyDecision(
                allowed=False,
                operation=operation,
                reason=(
                    "Ship Offline blocks all outbound network operations. "
                    "The task should be queued until the profile changes."
                ),
            )

        if operation == Operation.DOWNLOAD_METADATA:
            if not self.config.network.allow_metadata_downloads:
                return PolicyDecision(
                    allowed=False,
                    operation=operation,
                    reason="Metadata downloads are disabled by network policy.",
                )

        if operation == Operation.REFRESH_JELLYFIN:
            if not self.config.network.allow_jellyfin_refresh:
                return PolicyDecision(
                    allowed=False,
                    operation=operation,
                    reason="Jellyfin refreshes are disabled by network policy.",
                )

        if self.profile == "ship_limited":
            return PolicyDecision(
                allowed=True,
                operation=operation,
                reason=(
                    "Operation is permitted under Ship Limited network "
                    "restrictions."
                ),
                vpn_required=self.config.network.require_vpn,
                limited=True,
            )

        return PolicyDecision(
            allowed=True,
            operation=operation,
            reason="Operation is permitted under the Normal profile.",
            vpn_required=self.config.network.require_vpn,
            limited=self.low_impact,
        )

    def can(self, operation: Operation) -> bool:
        """Return only the allowed state for simple callers."""

        return self.decide(operation).allowed

    def can_use_network(self) -> bool:
        return self.can(Operation.USE_NETWORK)

    def can_download(self) -> bool:
        return self.can(Operation.DOWNLOAD_MEDIA)

    def can_download_metadata(self) -> bool:
        return self.can(Operation.DOWNLOAD_METADATA)

    def can_refresh_jellyfin(self) -> bool:
        return self.can(Operation.REFRESH_JELLYFIN)

    def can_import(self) -> bool:
        return self.can(Operation.IMPORT_MEDIA)

    def can_repair(self) -> bool:
        return self.can(Operation.REPAIR_MEDIA)

    def can_restore(self) -> bool:
        return self.can(Operation.RESTORE_MEDIA)

    def can_delete(self) -> bool:
        return self.can(Operation.DELETE_MEDIA)

    def require_operator_approval(self, operation: Operation) -> bool:
        return self.decide(operation).approval_required
