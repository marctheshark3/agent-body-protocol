"""Deterministic Agent Body Protocol event-to-HAL mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class BodyOutput:
    markers: tuple[str, ...]
    speech: str | None = None


def _marker(path: str, payload: Mapping[str, Any] | None = None) -> str:
    body = json.dumps(payload or {}, separators=(",", ":"), sort_keys=True)
    return f"[HW:{path}:{body}]"


def _effect(effect: str, color: list[int], *, speed: float = 1.0, duration_ms: int | None = None) -> str:
    payload: dict[str, Any] = {
        "color": color,
        "effect": effect,
        "speed": speed,
        "transient": True,
    }
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    return _marker("/led/effect", payload)


def map_event(event: Mapping[str, Any]) -> BodyOutput:
    """Map one validated protocol event to an exact ordered body sequence."""
    name = str(event["event"])
    mode = str(event.get("mode", "normal"))
    consent = str(event.get("consent", "ask"))
    quiet = mode in {"focus", "night"}

    if name == "started":
        return BodyOutput((
            _marker("/led/effect/stop", {"transient": True}),
            _marker("/led/solid", {"color": [48, 48, 48], "transient": True}),
        ))
    if name == "thinking":
        return BodyOutput((_effect("breathing", [0, 80, 255], speed=0.3),))
    if name == "waiting_for_user":
        return BodyOutput((
            _marker("/servo/aim", {"direction": "user"}),
            _effect("pulse", [255, 150, 0], speed=0.5),
        ))
    if name == "permission_required":
        return BodyOutput((
            _marker("/emotion", {"emotion": "listening", "intensity": 0.6}),
            _marker("/servo/aim", {"direction": "user"}),
            _effect("pulse", [255, 150, 0], speed=0.7),
        ), None if quiet else "Do you want to allow that?")
    if name == "blocked":
        return BodyOutput((
            _marker("/servo/aim", {"direction": "user"}),
            _effect("breathing", [255, 0, 0], speed=0.45),
        ), None if quiet or consent == "off" else "Want help with that?")
    if name == "tests_passed":
        # LED-only in v0: no raw pitch or unsafe nod pose.
        return BodyOutput((
            _marker("/led/effect/stop", {"transient": True}),
            _marker("/led/solid", {"color": [0, 200, 80], "transient": True}),
        ), None if quiet else "Tests passed.")
    if name == "tests_failed":
        return BodyOutput((
            _marker("/servo/aim", {"direction": "user"}),
            _effect("notification_flash", [255, 0, 0], speed=1.0, duration_ms=3000),
        ), None if quiet else "Tests failed.")
    if name == "completed":
        return BodyOutput((
            _marker("/servo/play", {"recording": "happy_wiggle"}),
            _effect("pulse", [0, 200, 80], speed=1.2, duration_ms=2000),
        ))
    if name == "quiet":
        return BodyOutput((
            _marker("/tts/stop"),
            _marker("/led/effect/stop", {"transient": True}),
            _marker("/led/restore"),
        ))
    raise ValueError(f"unsupported event: {name}")
