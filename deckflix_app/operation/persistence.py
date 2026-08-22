from datetime import datetime
import json
from pathlib import Path

from deckflix_app.decision import (
    Action,
    ApprovalItem,
    ApprovalPlan,
    ApprovalStatus,
    Decision,
    DecisionQueue,
    DecisionQueueItem,
)
from deckflix_app.metadata.models import MediaMetadata

from .ledger import (
    SnapshotDisposition,
    SnapshotLedger,
)
from .final_safety import FinalSafetyCertificate
from .manager import OperationManager
from .models import (
    Operation,
    OperationState,
    ShuttleSnapshot,
    SnapshotFile,
)


PERSISTENCE_VERSION = 3
SUPPORTED_PERSISTENCE_VERSIONS = {
    1,
    2,
    3,
}


def _media_to_dict(
    media: MediaMetadata | None,
) -> dict | None:
    if media is None:
        return None

    return {
        "media_type": media.media_type,
        "title": media.title,
        "year": media.year,
        "season": media.season,
        "episode": media.episode,
        "content_type": getattr(
            media,
            "content_type",
            None,
        ),
        "resolution": media.resolution,
        "source": media.source,
        "video_codec": media.video_codec,
        "container": media.container,
        "path": (
            str(media.path)
            if media.path is not None
            else None
        ),
        "size": media.size,
    }


def _media_from_dict(
    data: dict | None,
) -> MediaMetadata | None:
    if data is None:
        return None

    media_path = data.get(
        "path"
    )

    return MediaMetadata(
        media_type=data["media_type"],
        title=data["title"],
        year=data.get("year"),
        season=data.get("season"),
        episode=data.get("episode"),
        content_type=data.get(
            "content_type"
        ),
        resolution=data.get("resolution"),
        source=data.get("source"),
        video_codec=data.get("video_codec"),
        container=data.get("container"),
        path=(
            Path(media_path)
            if media_path
            else None
        ),
        size=int(
            data.get(
                "size",
                0,
            )
        ),
    )


def _decision_to_dict(
    decision: Decision,
) -> dict:
    return {
        "action": decision.action.value,
        "reason": decision.reason,
        "existing_score": decision.existing_score,
        "incoming_score": decision.incoming_score,
        "confidence": decision.confidence,
    }


def _decision_from_dict(
    data: dict,
) -> Decision:
    return Decision(
        action=Action(
            data["action"]
        ),
        reason=data["reason"],
        existing_score=int(
            data["existing_score"]
        ),
        incoming_score=int(
            data["incoming_score"]
        ),
        confidence=int(
            data.get(
                "confidence",
                100,
            )
        ),
    )


def _queue_item_to_dict(
    item: DecisionQueueItem,
) -> dict:
    return {
        "incoming": _media_to_dict(
            item.incoming
        ),
        "existing": _media_to_dict(
            item.existing
        ),
        "decision": _decision_to_dict(
            item.decision
        ),
    }


def _queue_item_from_dict(
    data: dict,
) -> DecisionQueueItem:
    incoming = _media_from_dict(
        data["incoming"]
    )

    if incoming is None:
        raise ValueError(
            "Saved decision has no incoming media"
        )

    return DecisionQueueItem(
        incoming=incoming,
        existing=_media_from_dict(
            data.get("existing")
        ),
        decision=_decision_from_dict(
            data["decision"]
        ),
    )


def _operation_to_dict(
    operation: Operation,
) -> dict:
    snapshot = operation.snapshot

    return {
        "id": operation.id,
        "state": operation.state.value,
        "created_at": (
            operation.created_at.isoformat()
        ),
        "snapshot": {
            "shuttle_path": str(
                snapshot.shuttle_path
            ),
            "device_id": snapshot.device_id,
            "total_bytes": snapshot.total_bytes,
            "fingerprint": snapshot.fingerprint,
            "created_at": (
                snapshot.created_at.isoformat()
            ),
            "files": [
                {
                    "relative_path": str(
                        item.relative_path
                    ),
                    "size": item.size,
                    "modified_ns": (
                        item.modified_ns
                    ),
                }
                for item in snapshot.files
            ],
        },
    }


def _operation_from_dict(
    data: dict,
) -> Operation:
    snapshot_data = data[
        "snapshot"
    ]

    snapshot = ShuttleSnapshot(
        shuttle_path=Path(
            snapshot_data[
                "shuttle_path"
            ]
        ),
        device_id=int(
            snapshot_data[
                "device_id"
            ]
        ),
        files=tuple(
            SnapshotFile(
                relative_path=Path(
                    item[
                        "relative_path"
                    ]
                ),
                size=int(
                    item[
                        "size"
                    ]
                ),
                modified_ns=int(
                    item[
                        "modified_ns"
                    ]
                ),
            )
            for item
            in snapshot_data[
                "files"
            ]
        ),
        total_bytes=int(
            snapshot_data[
                "total_bytes"
            ]
        ),
        fingerprint=(
            snapshot_data[
                "fingerprint"
            ]
        ),
        created_at=(
            datetime.fromisoformat(
                snapshot_data[
                    "created_at"
                ]
            )
        ),
    )

    return Operation(
        id=data["id"],
        state=OperationState(
            data["state"]
        ),
        snapshot=snapshot,
        created_at=(
            datetime.fromisoformat(
                data["created_at"]
            )
        ),
    )


def _ledger_to_dict(
    ledger: SnapshotLedger | None,
) -> list[dict]:
    if ledger is None:
        return []

    return [
        {
            "relative_path": str(
                entry.relative_path
            ),
            "disposition": (
                entry.disposition.value
            ),
            "evidence_path": (
                str(entry.evidence_path)
                if entry.evidence_path
                is not None
                else None
            ),
            "sha256": entry.sha256,
            "detail": entry.detail,
        }
        for entry in sorted(
            ledger.entries.values(),
            key=lambda item: (
                item.relative_path
                .as_posix()
                .casefold()
            ),
        )
    ]


def _ledger_from_dict(
    snapshot: ShuttleSnapshot,
    data: list[dict] | None,
) -> SnapshotLedger:
    ledger = (
        SnapshotLedger.from_snapshot(
            snapshot
        )
    )

    if not data:
        return ledger

    for item in data:
        relative_path = Path(
            item[
                "relative_path"
            ]
        )

        evidence = item.get(
            "evidence_path"
        )

        ledger.set(
            relative_path,
            SnapshotDisposition(
                item[
                    "disposition"
                ]
            ),
            evidence_path=(
                Path(evidence)
                if evidence
                else None
            ),
            sha256=item.get(
                "sha256"
            ),
            detail=item.get(
                "detail",
                "",
            ),
        )

    return ledger


def _final_safety_certificate_to_dict(
    certificate: FinalSafetyCertificate | None,
) -> dict | None:
    if certificate is None:
        return None

    return {
        "operation_id": certificate.operation_id,
        "snapshot_fingerprint": (
            certificate.snapshot_fingerprint
        ),
        "snapshot_device_id": (
            certificate.snapshot_device_id
        ),
        "evidence_fingerprint": (
            certificate.evidence_fingerprint
        ),
        "snapshot_files": certificate.snapshot_files,
        "imported": certificate.imported,
        "identical": certificate.identical,
        "superseded": certificate.superseded,
        "review_hold": certificate.review_hold,
        "unresolved": certificate.unresolved,
        "validated_at": (
            certificate.validated_at.isoformat()
        ),
    }


def _final_safety_certificate_from_dict(
    data: dict | None,
) -> FinalSafetyCertificate | None:
    if not data:
        return None

    return FinalSafetyCertificate(
        operation_id=data["operation_id"],
        snapshot_fingerprint=(
            data["snapshot_fingerprint"]
        ),
        snapshot_device_id=int(
            data["snapshot_device_id"]
        ),
        evidence_fingerprint=(
            data["evidence_fingerprint"]
        ),
        snapshot_files=int(
            data["snapshot_files"]
        ),
        imported=int(
            data["imported"]
        ),
        identical=int(
            data["identical"]
        ),
        superseded=int(
            data.get(
                "superseded",
                0,
            )
        ),
        review_hold=int(
            data["review_hold"]
        ),
        unresolved=int(
            data["unresolved"]
        ),
        validated_at=datetime.fromisoformat(
            data["validated_at"]
        ),
    )


def manager_to_dict(
    manager: OperationManager,
) -> dict:
    operation = (
        manager.require_operation()
    )

    decisions = manager.decisions
    approval_plan = (
        manager.approval_plan
    )

    queue_items = (
        decisions.items
        if decisions is not None
        else []
    )

    approval_statuses = (
        [
            item.status.value
            for item
            in approval_plan.items
        ]
        if approval_plan
        is not None
        else []
    )

    return {
        "version": (
            PERSISTENCE_VERSION
        ),
        "operation": (
            _operation_to_dict(
                operation
            )
        ),
        "decisions": [
            _queue_item_to_dict(
                item
            )
            for item in queue_items
        ],
        "approval_statuses": (
            approval_statuses
        ),
        "ledger": (
            _ledger_to_dict(
                manager.ledger
            )
        ),
        "import_authorized": (
            manager.import_authorized
        ),
        "final_safety_certificate": (
            _final_safety_certificate_to_dict(
                manager.final_safety_certificate
            )
        ),
    }


def manager_from_dict(
    data: dict,
) -> OperationManager:
    version = int(
        data.get(
            "version",
            0,
        )
    )

    if (
        version
        not in SUPPORTED_PERSISTENCE_VERSIONS
    ):
        raise ValueError(
            "Unsupported operation "
            "persistence version"
        )

    manager = (
        OperationManager()
    )

    manager.operation = (
        _operation_from_dict(
            data[
                "operation"
            ]
        )
    )

    decision_items = [
        _queue_item_from_dict(
            item
        )
        for item in data.get(
            "decisions",
            [],
        )
    ]

    if decision_items:
        manager.decisions = (
            DecisionQueue(
                items=decision_items
            )
        )

    manager.import_authorized = bool(
        data.get(
            "import_authorized",
            False,
        )
    )

    statuses = data.get(
        "approval_statuses",
        [],
    )

    if statuses:
        if (
            len(statuses)
            != len(decision_items)
        ):
            raise ValueError(
                "Saved approval plan "
                "does not match "
                "decision queue"
            )

        manager.approval_plan = (
            ApprovalPlan(
                items=[
                    ApprovalItem(
                        queue_item=(
                            queue_item
                        ),
                        status=(
                            ApprovalStatus(
                                status
                            )
                        ),
                    )
                    for (
                        queue_item,
                        status,
                    )
                    in zip(
                        decision_items,
                        statuses,
                        strict=True,
                    )
                ]
            )
        )

    operation = (
        manager.require_operation()
    )

    # Version-1 state files did not contain a ledger.
    # Loading them is intentionally conservative:
    # every snapshot file starts UNRESOLVED.
    manager.ledger = (
        _ledger_from_dict(
            operation.snapshot,
            (
                data.get(
                    "ledger"
                )
                if version >= 2
                else None
            ),
        )
    )

    if version >= 3:
        manager.final_safety_certificate = (
            _final_safety_certificate_from_dict(
                data.get(
                    "final_safety_certificate"
                )
            )
        )

    return manager


def save_operation_manager(
    manager: OperationManager,
    destination: Path,
) -> Path:
    destination = Path(
        destination
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        destination.with_suffix(
            destination.suffix
            + ".tmp"
        )
    )

    temporary.write_text(
        json.dumps(
            manager_to_dict(
                manager
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        destination
    )

    return destination


def load_operation_manager(
    source: Path,
) -> OperationManager:
    source = Path(
        source
    )

    if not source.exists():
        return OperationManager()

    data = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    return manager_from_dict(
        data
    )


def delete_saved_operation(
    source: Path,
) -> None:
    source = Path(
        source
    )

    try:
        source.unlink()
    except FileNotFoundError:
        pass
