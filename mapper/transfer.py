"""Replay logged [HW:] onto another HAL and measure pose/LED gap.

This is API-level sim-to-real: same markers, different body.
Not Isaac. Not a trained policy.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .hal_client import dispatch
from .motion import FORBIDDEN
from .trajectory import JOINTS, load_rows, read_body, record

THRESHOLD_DEG = 5.0
SETTLE_S = 0.8
YAW_ONLY = {"left", "right"}


class TransferError(ValueError):
    pass


def _direction(row: dict[str, Any]) -> str | None:
    command = row.get("command") or {}
    nested = command.get("source_command") or command
    name = nested.get("direction")
    if name:
        return str(name).lower()
    blob = "".join(row.get("markers") or [])
    for token in YAW_ONLY | {"center", "desk", "wall", "up", "down", "user"}:
        if f'"direction":"{token}"' in blob:
            return token
    return None


def scored_joints(row: dict[str, Any]) -> tuple[str, ...]:
    """HAL mock/animation: left/right only pan yaw; other aims keep current yaw."""
    direction = _direction(row)
    if direction in YAW_ONLY:
        return ("base_yaw.pos",)
    if direction:
        return tuple(name for name in JOINTS if name != "base_yaw.pos")
    return JOINTS


def joint_delta(expected: dict[str, Any] | None, actual: dict[str, Any] | None, names: tuple[str, ...] = JOINTS) -> dict[str, float]:
    exp = (expected or {}).get("positions") or {}
    act = (actual or {}).get("positions") or {}
    out: dict[str, float] = {}
    for name in names:
        if exp.get(name) is None or act.get(name) is None:
            continue
        out[name] = abs(float(act[name]) - float(exp[name]))
    return out


def assert_safe_markers(markers: list[str]) -> None:
    blob = "".join(markers).lower()
    for token in FORBIDDEN:
        if token.lower() in blob:
            raise TransferError(f"refusing to replay forbidden token: {token}")


def led_match(expected: dict[str, Any] | None, actual: dict[str, Any] | None) -> bool:
    exp = ((expected or {}).get("led") or {}).get("hex")
    act = ((actual or {}).get("led") or {}).get("hex")
    if not exp or not act:
        return True
    return str(exp).lower() == str(act).lower()


def replay_row(row: dict[str, Any], hal_url: str, out: Path, house: str, settle_s: float = SETTLE_S) -> dict[str, Any]:
    markers = list(row.get("markers") or [])
    assert_safe_markers(markers)
    before = read_body(hal_url)
    dispatched = dispatch(markers, hal_url) if markers else []
    if dispatched and settle_s > 0:
        time.sleep(settle_s)
    after = read_body(hal_url)
    deltas = joint_delta(row.get("after"), after, scored_joints(row))
    gap = {
        "max_joint_deg": max(deltas.values()) if deltas else 0.0,
        "joints": deltas,
        "led_hex_match": led_match(row.get("after"), after),
        "within_threshold": all(v < THRESHOLD_DEG for v in deltas.values()),
    }
    logged = record(
        out,
        house=house,
        kind="replay",
        command={"source_kind": row.get("kind"), "source_command": row.get("command")},
        markers=markers,
        dispatched=dispatched,
        before=before,
        after={**after, "gap": gap},
        source="transfer",
    )
    logged["gap"] = gap
    return logged


def replay(log_path: Path, hal_url: str, out: Path, house: str = "transfer", settle_s: float = SETTLE_S) -> dict[str, Any]:
    rows = load_rows(log_path)
    results = [replay_row(row, hal_url, out, house, settle_s) for row in rows]
    ok = bool(results) and all(item["gap"]["within_threshold"] for item in results)
    return {
        "ok": ok,
        "count": len(results),
        "threshold_deg": THRESHOLD_DEG,
        "failures": [i for i, item in enumerate(results) if not item["gap"]["within_threshold"]],
        "results": results,
    }
