"""Sealed vendor channel: signed software in, nothing out."""

from __future__ import annotations

from typing import Any

from .presence import OWNER
from .receipts import ReceiptStore
from .record import CustodyRecord

VENDOR_CAMERA = "vendor.camera"
VENDOR_MIC = "vendor.mic"
VENDOR_LOGS = "vendor.logs"
VENDOR_ACTUATE = "vendor.actuate"
VENDOR_OTA = "vendor.ota"

PULLS = frozenset({VENDOR_CAMERA, VENDOR_MIC, VENDOR_LOGS, VENDOR_ACTUATE})


def freeze(record: CustodyRecord, subject: str) -> bool:
    if subject != OWNER:
        return False
    record.ota_frozen = True
    return True


def unfreeze(record: CustodyRecord, subject: str) -> bool:
    if subject != OWNER:
        return False
    record.ota_frozen = False
    return True


def apply_update(
    record: CustodyRecord,
    store: ReceiptStore,
    *,
    artifact: str,
    signed: bool,
    subject: str = "vendor",
    prompt: str | None = None,
) -> dict[str, Any]:
    del prompt
    leftover_was_closed = record.leftover_closed
    if subject == OWNER:
        reason = "owner-does-not-apply"
    elif not signed:
        reason = "unsigned"
    elif record.ota_frozen:
        reason = "frozen"
    else:
        record.last_applied = artifact
        if leftover_was_closed:
            record.leftover_closed = True
        receipt = store.issue(VENDOR_OTA, record.owner or "unknown", source=artifact)
        return {
            "ok": True,
            "artifact": artifact,
            "leftover_closed": record.leftover_closed,
            "receipt": None if receipt is None else receipt.to_json(),
        }
    receipt = store.issue(f"{VENDOR_OTA}.{reason}", record.owner or "unknown", source=artifact)
    return {
        "ok": False,
        "reason": reason,
        "leftover_closed": record.leftover_closed,
        "receipt": None if receipt is None else receipt.to_json(),
    }


def pull(record: CustodyRecord, store: ReceiptStore, channel: str) -> dict[str, Any]:
    if channel not in PULLS:
        channel = VENDOR_LOGS
    receipt = store.issue(channel, record.owner or "unknown")
    return {
        "ok": False,
        "channel": channel,
        "receipt": None if receipt is None else receipt.to_json(),
    }
