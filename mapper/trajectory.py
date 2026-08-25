"""Append command/state pairs. Dataset for later sim-to-real, not a model."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .hal_client import assert_hal_url

SCHEMA = "abp.trajectory/v1"
JOINTS = (
    "base_yaw.pos",
    "base_pitch.pos",
    "elbow_pitch.pos",
    "wrist_pitch.pos",
    "wrist_roll.pos",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_json(hal_url: str, path: str, timeout: float = 3.0) -> dict[str, Any]:
    base = assert_hal_url(hal_url)
    request = Request(base + path, method="GET")
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return json.loads(raw) if raw else {}


def read_body(hal_url: str | None) -> dict[str, Any]:
    if not hal_url:
        return {"ok": False, "error": "no_hal"}
    assert_hal_url(hal_url)
    try:
        led = get_json(hal_url, "/led/color")
        servo = get_json(hal_url, "/servo/position")
        try:
            sim = get_json(hal_url, "/simulator/state")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            sim = None
        positions = servo.get("positions") or {}
        return {
            "ok": True,
            "led": {
                "color": led.get("color"),
                "hex": led.get("hex"),
                "effect": led.get("effect"),
                "on": led.get("on"),
            },
            "positions": {name: positions.get(name) for name in JOINTS},
            "simulator": sim,
        }
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}


def record(
    path: Path,
    *,
    house: str,
    kind: str,
    command: dict[str, Any],
    markers: list[str],
    dispatched: list[dict[str, Any]] | None,
    before: dict[str, Any],
    after: dict[str, Any],
    source: str = "hal_simulate",
) -> dict[str, Any]:
    row = {
        "schema": SCHEMA,
        "ts": utc_now(),
        "house": house,
        "kind": kind,
        "source": source,
        "command": command,
        "markers": list(markers),
        "dispatched": list(dispatched or []),
        "before": before,
        "after": after,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, separators=(",", ":")) + "\n")
    return row


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
