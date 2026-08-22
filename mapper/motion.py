"""Named aim intents only. No raw joints. No tenth event."""

from __future__ import annotations

import os
from collections.abc import Callable

ALLOWED_DIRECTIONS = (
    "center",
    "desk",
    "wall",
    "left",
    "right",
    "up",
    "down",
    "user",
)

FORBIDDEN = (
    "base_yaw",
    "base_pitch",
    "elbow_pitch",
    "wrist_pitch",
    "wrist_roll",
    "/servo/set",
    "set_joint",
    "nudge",
)


class MotionError(ValueError):
    pass


def validate_markers(markers: list[str]) -> list[str]:
    blob = "".join(markers).lower()
    for token in FORBIDDEN:
        if token.lower() in blob:
            raise MotionError(f"motion policy emitted forbidden token: {token}")
    if len(markers) != 1:
        raise MotionError("motion policy must emit exactly one marker")
    marker = markers[0]
    if not marker.startswith("[HW:/servo/aim:"):
        raise MotionError("motion policy must emit /servo/aim")
    return markers


def named_aim(direction: str) -> list[str]:
    name = str(direction or "").strip().lower()
    if name not in ALLOWED_DIRECTIONS:
        raise MotionError(f"unknown aim direction: {direction!r}")
    return validate_markers([f'[HW:/servo/aim:{{"direction":"{name}"}}]'])


AimPolicy = Callable[[str], list[str]]


def load_policy(name: str | None = None) -> AimPolicy:
    choice = (name or os.environ.get("ABP_AIM_POLICY") or "named").strip().lower()
    if choice in {"", "named", "default", "hal"}:
        return named_aim
    if choice == "learned":
        # Slot only. A later module may register here. Missing → named fallback.
        try:
            from mapper.learned_aim import learned_aim  # type: ignore
        except ImportError:
            return named_aim
        return learned_aim
    raise MotionError(f"unknown aim policy: {choice}")


def aim(direction: str, policy: AimPolicy | None = None) -> list[str]:
    return (policy or load_policy())(direction)
