"""In-process Lamp body for two-house demos. Not a second HAL."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from .hal_client import parse_marker
from .map import map_event

AIM = {
    "user": {
        "base_yaw.pos": 0.0,
        "base_pitch.pos": 0.0,
        "elbow_pitch.pos": 0.0,
        "wrist_roll.pos": 0.0,
        "wrist_pitch.pos": -85.0,
    },
    "center": {
        "base_yaw.pos": 3.0,
        "base_pitch.pos": -20.0,
        "elbow_pitch.pos": 32.0,
        "wrist_roll.pos": 0.0,
        "wrist_pitch.pos": 0.0,
    },
    "left": {
        "base_yaw.pos": -90.0,
        "base_pitch.pos": -30.0,
        "elbow_pitch.pos": 57.0,
        "wrist_roll.pos": 0.0,
        "wrist_pitch.pos": 18.0,
    },
    "right": {
        "base_yaw.pos": 90.0,
        "base_pitch.pos": -30.0,
        "elbow_pitch.pos": 57.0,
        "wrist_roll.pos": 0.0,
        "wrist_pitch.pos": 18.0,
    },
}
WIGGLE = {
    "base_yaw.pos": 18.0,
    "base_pitch.pos": -8.0,
    "elbow_pitch.pos": 40.0,
    "wrist_roll.pos": 20.0,
    "wrist_pitch.pos": 12.0,
}
REST = {
    "base_yaw.pos": 0.0,
    "base_pitch.pos": -12.0,
    "elbow_pitch.pos": 20.0,
    "wrist_roll.pos": 0.0,
    "wrist_pitch.pos": 0.0,
}


def _event(name: str) -> dict:
    return {
        "v": 1,
        "event": name,
        "ts": "2026-01-01T00:00:00Z",
        "source": "manual",
        "mode": "normal",
        "consent": "ask",
    }


@dataclass
class VirtualBody:
    house: str
    event: str | None = None
    color: list[int] = field(default_factory=lambda: [0, 0, 0])
    effect: str | None = None
    pose: dict[str, float] = field(default_factory=lambda: dict(REST))
    speech: str | None = None

    def apply_markers(self, markers: list[str], label: str | None = None) -> dict:
        if label:
            self.event = label
        for marker in markers:
            path, payload = parse_marker(marker)
            if path == "/led/solid":
                self.color = list(payload.get("color") or [0, 0, 0])
                self.effect = None
            elif path == "/led/effect":
                self.color = list(payload.get("color") or self.color)
                self.effect = str(payload.get("effect") or "pulse")
            elif path in {"/led/effect/stop", "/led/restore"}:
                self.effect = None
                if path == "/led/restore":
                    self.color = [0, 0, 0]
            elif path == "/servo/aim":
                self.pose = dict(AIM.get(str(payload.get("direction") or "center"), AIM["center"]))
            elif path == "/servo/play":
                self.pose = dict(WIGGLE)
            elif path == "/servo/track":
                self.pose = dict(AIM["user"])
        return self.snapshot()

    def apply(self, event_name: str) -> dict:
        output = map_event(_event(event_name))
        self.speech = output.speech
        return self.apply_markers(list(output.markers), event_name)

    def reset(self) -> None:
        self.event = None
        self.color = [0, 0, 0]
        self.effect = None
        self.pose = dict(REST)
        self.speech = None

    def snapshot(self) -> dict:
        return {
            "house": self.house,
            "event": self.event,
            "color": list(self.color),
            "hex": "#{:02x}{:02x}{:02x}".format(*[max(0, min(255, c)) for c in self.color]),
            "effect": self.effect,
            "pose": deepcopy(self.pose),
            "speech": self.speech,
        }
