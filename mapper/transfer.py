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


def expects_led(row: dict[str, Any]) -> bool:
    return any("/led/" in marker for marker in (row.get("markers") or []))


def scored_joints(row: dict[str, Any]) -> tuple[str, ...]:
    """Score only joints the markers actually command.

    HAL mock/animation: left/right only pan yaw; other aims keep current yaw.
    LED-only rows score no joints.
    """
    blob = "".join(row.get("markers") or [])
    direction = _direction(row)
    if "/servo/play" in blob:
        return JOINTS
    if "/servo/aim" not in blob and "/servo/track" not in blob:
        return ()
    if direction in YAW_ONLY:
        return ("base_yaw.pos",)
    if direction:
        return tuple(name for name in JOINTS if name != "base_yaw.pos")
    if "/servo/track" in blob:
        return tuple(name for name in JOINTS if name != "base_yaw.pos")
    return ()


def joint_delta(expected: dict[str, Any] | None, actual: dict[str, Any] | None, names: tuple[str, ...] = JOINTS) -> tuple[dict[str, float], tuple[str, ...]]:
    exp = (expected or {}).get("positions") or {}
    act = (actual or {}).get("positions") or {}
    out: dict[str, float] = {}
    missing: list[str] = []
    for name in names:
        if exp.get(name) is None or act.get(name) is None:
            missing.append(name)
            continue
        out[name] = abs(float(act[name]) - float(exp[name]))
    return out, tuple(missing)


def led_match(expected: dict[str, Any] | None, actual: dict[str, Any] | None, required: bool = False) -> bool:
    exp = ((expected or {}).get("led") or {}).get("hex")
    act = ((actual or {}).get("led") or {}).get("hex")
    if not exp or not act:
        return not required
    return str(exp).lower() == str(act).lower()


def assert_safe_markers(markers: list[str]) -> None:
    blob = "".join(markers).lower()
    for token in FORBIDDEN:
        if token.lower() in blob:
            raise TransferError(f"refusing to replay forbidden token: {token}")


def replay_row(row: dict[str, Any], hal_url: str, out: Path, house: str, settle_s: float = SETTLE_S) -> dict[str, Any]:
    markers = list(row.get("markers") or [])
    assert_safe_markers(markers)
    before = read_body(hal_url)
    dispatched = dispatch(markers, hal_url) if markers else []
    if dispatched and settle_s > 0:
        time.sleep(settle_s)
    after = read_body(hal_url)
    names = scored_joints(row)
    deltas, missing = joint_delta(row.get("after"), after, names)
    led_ok = led_match(row.get("after"), after, required=expects_led(row))
    pose_ok = not missing and all(v < THRESHOLD_DEG for v in deltas.values())
    gap = {
        "max_joint_deg": max(deltas.values()) if deltas else 0.0,
        "joints": deltas,
        "missing_joints": list(missing),
        "led_hex_match": led_ok,
        "within_threshold": pose_ok and led_ok,
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
