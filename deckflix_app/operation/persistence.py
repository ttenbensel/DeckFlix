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

from .manager import OperationManager
from .models import (
    Operation,
    OperationState,
    ShuttleSnapshot,
    SnapshotFile,
)


PERSISTENCE_VERSION = 1


def _media_to_dict(media: MediaMetadata | None) -> dict | None:
    if media is None:
        return None

    return {
        "media_type": media.media_type,
        "title": media.title,
        "year": media.year,
        "season": media.season,
        "episode": media.episode,
        "resolution": media.resolution,
        "source": media.source,
        "video_codec": media.video_codec,
        "container": media.container,
        "path": str(media.path) if media.path is not None else None,
        "size": media.size,
    }


def _media_from_dict(data: dict | None) -> MediaMetadata | None:
    if data is None:
        return None

    media_path = data.get("path")

    return MediaMetadata(
        media_type=data["media_type"],
        title=data["title"],
        year=data.get("year"),
        season=data.get("season"),
        episode=data.get("episode"),
        resolution=data.get("resolution"),
        source=data.get("source"),
        video_codec=data.get("video_codec"),
        container=data.get("container"),
        path=Path(media_path) if media_path else None,
        size=int(data.get("size", 0)),
    )


def _decision_to_dict(decision: Decision) -> dict:
    return {
        "action": decision.action.value,
        "reason": decision.reason,
        "existing_score": decision.existing_score,
        "incoming_score": decision.incoming_score,
        "confidence": decision.confidence,
    }


def _decision_from_dict(data: dict) -> Decision:
    return Decision(
        action=Action(data["action"]),
        reason=data["reason"],
        existing_score=int(data["existing_score"]),
        incoming_score=int(data["incoming_score"]),
        confidence=int(data.get("confidence", 100)),
    )


def _queue_item_to_dict(item: DecisionQueueItem) -> dict:
    return {
        "incoming": _media_to_dict(item.incoming),
        "existing": _media_to_dict(item.existing),
        "decision": _decision_to_dict(item.decision),
    }


def _queue_item_from_dict(data: dict) -> DecisionQueueItem:
    incoming = _media_from_dict(data["incoming"])

    if incoming is None:
        raise ValueError("Saved decision has no incoming media")

    return DecisionQueueItem(
        incoming=incoming,
        existing=_media_from_dict(data.get("existing")),
        decision=_decision_from_dict(data["decision"]),
    )


def _operation_to_dict(operation: Operation) -> dict:
    snapshot = operation.snapshot

    return {
        "id": operation.id,
        "state": operation.state.value,
        "created_at": operation.created_at.isoformat(),
        "snapshot": {
            "shuttle_path": str(snapshot.shuttle_path),
            "device_id": snapshot.device_id,
            "total_bytes": snapshot.total_bytes,
            "fingerprint": snapshot.fingerprint,
            "created_at": snapshot.created_at.isoformat(),
            "files": [
                {
                    "relative_path": str(item.relative_path),
                    "size": item.size,
                    "modified_ns": item.modified_ns,
                }
                for item in snapshot.files
            ],
        },
    }


def _operation_from_dict(data: dict) -> Operation:
    snapshot_data = data["snapshot"]

    snapshot = ShuttleSnapshot(
        shuttle_path=Path(snapshot_data["shuttle_path"]),
        device_id=int(snapshot_data["device_id"]),
        files=tuple(
            SnapshotFile(
                relative_path=Path(item["relative_path"]),
                size=int(item["size"]),
                modified_ns=int(item["modified_ns"]),
            )
            for item in snapshot_data["files"]
        ),
        total_bytes=int(snapshot_data["total_bytes"]),
        fingerprint=snapshot_data["fingerprint"],
        created_at=datetime.fromisoformat(
            snapshot_data["created_at"]
        ),
    )

    return Operation(
        id=data["id"],
        state=OperationState(data["state"]),
        snapshot=snapshot,
        created_at=datetime.fromisoformat(data["created_at"]),
    )


def manager_to_dict(manager: OperationManager) -> dict:
    operation = manager.require_operation()

    decisions = manager.decisions
    approval_plan = manager.approval_plan

    queue_items = (
        decisions.items
        if decisions is not None
        else []
    )

    approval_statuses = (
        [
            item.status.value
            for item in approval_plan.items
        ]
        if approval_plan is not None
        else []
    )

    return {
        "version": PERSISTENCE_VERSION,
        "operation": _operation_to_dict(operation),
        "decisions": [
            _queue_item_to_dict(item)
            for item in queue_items
        ],
        "approval_statuses": approval_statuses,
        "import_authorized": manager.import_authorized,
    }


def manager_from_dict(data: dict) -> OperationManager:
    if int(data.get("version", 0)) != PERSISTENCE_VERSION:
        raise ValueError("Unsupported operation persistence version")

    manager = OperationManager()
    manager.operation = _operation_from_dict(data["operation"])

    decision_items = [
        _queue_item_from_dict(item)
        for item in data.get("decisions", [])
    ]

    if decision_items:
        manager.decisions = DecisionQueue(
            items=decision_items
        )

    manager.import_authorized = bool(
        data.get("import_authorized", False)
    )

    statuses = data.get("approval_statuses", [])

    if statuses:
        if len(statuses) != len(decision_items):
            raise ValueError(
                "Saved approval plan does not match decision queue"
            )

        manager.approval_plan = ApprovalPlan(
            items=[
                ApprovalItem(
                    queue_item=queue_item,
                    status=ApprovalStatus(status),
                )
                for queue_item, status in zip(
                    decision_items,
                    statuses,
                    strict=True,
                )
            ]
        )

    return manager


def save_operation_manager(
    manager: OperationManager,
    destination: Path,
) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            manager_to_dict(manager),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(destination)

    return destination


def load_operation_manager(
    source: Path,
) -> OperationManager:
    source = Path(source)

    if not source.exists():
        return OperationManager()

    data = json.loads(
        source.read_text(encoding="utf-8")
    )

    return manager_from_dict(data)


def delete_saved_operation(source: Path) -> None:
    source = Path(source)

    try:
        source.unlink()
    except FileNotFoundError:
        pass
