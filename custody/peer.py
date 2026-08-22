"""Optical peer channel: robots speak in the room, not over leftover."""

from __future__ import annotations

from typing import Any

from .receipts import ReceiptStore
from .record import CustodyRecord
from .vendor import apply_update

PEER_CAMERA = "peer.camera"
PEER_MIC = "peer.mic"
PEER_SERVO = "peer.servo"
PEER_EVENT = "peer.event"
PEER_ARTIFACT = "peer.artifact"

MEDIA = frozenset({"led", "ir", "wire"})
SENSORS = frozenset({PEER_CAMERA, PEER_MIC, PEER_SERVO})
EVENTS = frozenset(
    {
        "started",
        "thinking",
        "waiting_for_user",
        "permission_required",
        "blocked",
        "tests_passed",
        "tests_failed",
        "completed",
        "quiet",
    }
)


def accept(
    record: CustodyRecord,
    store: ReceiptStore,
    *,
    kind: str,
    media: str,
    event: str | None = None,
    artifact: str | None = None,
    signed: bool = False,
    prompt: str | None = None,
) -> dict[str, Any]:
    """A peer may offer an ABP event or a sealed artifact. Never sensors."""
    del prompt
    if media not in MEDIA:
        receipt = store.issue("peer.bad-media", record.owner or "unknown", source=media)
        return {"ok": False, "reason": "bad-media", "receipt": _json(receipt)}
    if kind in {"camera", "mic", "servo"} or kind in SENSORS:
        channel = {
            "camera": PEER_CAMERA,
            "mic": PEER_MIC,
            "servo": PEER_SERVO,
        }.get(kind, kind)
        receipt = store.issue(channel, record.owner or "unknown", source=media)
        return {"ok": False, "reason": "sensor", "channel": channel, "receipt": _json(receipt)}
    if kind == "event":
        if event not in EVENTS:
            receipt = store.issue("peer.bad-event", record.owner or "unknown", source=media)
            return {"ok": False, "reason": "bad-event", "receipt": _json(receipt)}
        leftover = record.leftover_closed
        receipt = store.issue(PEER_EVENT, record.owner or "unknown", source=f"{media}:{event}")
        return {
            "ok": True,
            "kind": "event",
            "event": event,
            "media": media,
            "leftover_closed": leftover,
            "receipt": _json(receipt),
        }
    if kind == "artifact":
        result = apply_update(
            record,
            store,
            artifact=artifact or "peer-artifact",
            signed=signed,
            subject="vendor",
        )
        result["media"] = media
        result["kind"] = "artifact"
        return result
    receipt = store.issue("peer.bad-kind", record.owner or "unknown", source=media)
    return {"ok": False, "reason": "bad-kind", "receipt": _json(receipt)}


def _json(receipt: Any) -> dict[str, Any] | None:
    return None if receipt is None else receipt.to_json()
