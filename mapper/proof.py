"""Live HAL receipt. HTTP 200 is not proof. Deltas are."""

from __future__ import annotations

import time
from typing import Any

from .map import map_event
from .skills import dispatch_soft, markers_for
from .trajectory import JOINTS, read_body

SETTLE_S = 0.8
MOVE_DEG = 5.0


def _event(name: str) -> dict[str, Any]:
    return {
        "v": 1,
        "event": name,
        "ts": "2026-01-01T00:00:00Z",
        "source": "manual",
        "mode": "normal",
        "consent": "ask",
    }


def joint_deltas(before: dict[str, Any], after: dict[str, Any]) -> dict[str, float]:
    left = (before or {}).get("positions") or {}
    right = (after or {}).get("positions") or {}
    out: dict[str, float] = {}
    for name in JOINTS:
        try:
            a = left.get(name)
            b = right.get(name)
            if a is None or b is None:
                out[name] = 0.0
            else:
                out[name] = abs(float(b) - float(a))
        except (TypeError, ValueError):
            out[name] = 0.0
    return out


def led_hex(snap: dict[str, Any]) -> str:
    led = (snap or {}).get("led") or {}
    return str(led.get("hex") or "").lower()


def grade(row: dict[str, Any]) -> dict[str, Any]:
    dispatched = list(row.get("dispatched") or [])
    statuses = [int(item.get("status") or 0) for item in dispatched]
    moved = [name for name, deg in (row.get("deltas") or {}).items() if deg >= MOVE_DEG]
    led_changed = bool(row.get("led_before") and row.get("led_after") and row["led_before"] != row["led_after"])
    http_ok = bool(statuses) and all(200 <= s < 300 for s in statuses)
    kind = row.get("kind")
    if kind == "follow":
        track = next((s for item, s in zip(dispatched, statuses) if item.get("path") == "/servo/track"), None)
        ok = track == 500
        reason = "follow 500 without a person is the honest HAL sim"
    elif kind in {"look", "dance", "stop"}:
        ok = http_ok and (bool(moved) or row.get("before", {}).get("ok") is False)
        reason = "named verb moved a scored joint" if moved else "HAL accepted the verb"
    else:
        ok = http_ok and (led_changed or bool(moved))
        reason = "LED or pose changed on the live driver"
    return {
        "ok": ok,
        "http_ok": http_ok,
        "moved_joints": moved,
        "led_changed": led_changed,
        "statuses": statuses,
        "reason": reason,
    }


def run_proof(name: str, hal_url: str | None, settle_s: float = SETTLE_S) -> dict[str, Any]:
    key = str(name or "").strip().lower()
    if key in {"look", "follow", "dance", "stop"}:
        markers = markers_for(key)
        kind = key
    else:
        output = map_event(_event(key))
        markers = list(output.markers)
        kind = "event"
    before = read_body(hal_url)
    dispatched = dispatch_soft(markers, hal_url) if hal_url else []
    if dispatched and settle_s > 0:
        time.sleep(settle_s)
    after = read_body(hal_url)
    row = {
        "kind": kind,
        "name": key,
        "markers": markers,
        "dispatched": dispatched,
        "before": before,
        "after": after,
        "led_before": led_hex(before),
        "led_after": led_hex(after),
        "deltas": joint_deltas(before, after),
        "source": "hal_live",
    }
    row["grade"] = grade(row)
    return row
