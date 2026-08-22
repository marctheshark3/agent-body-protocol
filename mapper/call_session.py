"""Consented two-house call mapped onto the nine ABP events.

This is a skill, not a tenth event. Video never rides these events.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Literal

House = Literal["near", "far"]
Phase = Literal["idle", "confirm", "ringing", "in_call", "ended"]

# Public fixtures use synthetic names only.
CONTACT = "Sam"

NEAR_EVENTS = {
    "confirm": "permission_required",
    "ringing": "waiting_for_user",
    "accept": "quiet",
    "decline": "quiet",
    "hangup": "quiet",
}
FAR_EVENTS = {
    "confirm": None,
    "ringing": "permission_required",
    "accept": "quiet",
    "decline": "quiet",
    "hangup": "quiet",
}


@dataclass
class HouseState:
    house: House
    event: str | None = None
    screen_open: bool = False
    camera_on: bool = False
    mic_on: bool = False


@dataclass
class CallSession:
    contact: str = CONTACT
    phase: Phase = "idle"
    near: HouseState = field(default_factory=lambda: HouseState("near"))
    far: HouseState = field(default_factory=lambda: HouseState("far"))
    media_allowed: bool = False

    def reset(self) -> None:
        self.phase = "idle"
        self.media_allowed = False
        self.near = HouseState("near")
        self.far = HouseState("far")

    def start(self) -> list[tuple[House, str]]:
        if self.phase == "ended":
            self.reset()
        if self.phase != "idle":
            raise ValueError("call already in progress")
        self.phase = "confirm"
        return self._apply("confirm")

    def invite(self) -> list[tuple[House, str]]:
        if self.phase != "confirm":
            raise ValueError("invite requires a local confirm")
        self.phase = "ringing"
        return self._apply("ringing")

    def dial(self) -> list[tuple[House, str]]:
        """One-click demo: the click is local confirm, then the far house rings."""
        emitted: list[tuple[House, str]] = []
        if self.phase in {"idle", "ended"}:
            emitted.extend(self.start())
        emitted.extend(self.invite())
        return emitted

    def accept(self) -> list[tuple[House, str]]:
        if self.phase != "ringing":
            raise ValueError("accept requires a ring")
        self.phase = "in_call"
        self.media_allowed = True
        self.near.screen_open = True
        self.far.screen_open = True
        self.near.camera_on = False
        self.far.camera_on = False
        return self._apply("accept")

    def decline(self) -> list[tuple[House, str]]:
        if self.phase not in {"confirm", "ringing"}:
            raise ValueError("nothing to decline")
        self.phase = "ended"
        self._close_media()
        return self._apply("decline")

    def hangup(self) -> list[tuple[House, str]]:
        if self.phase != "in_call":
            raise ValueError("hangup requires an active call")
        self.phase = "ended"
        self._close_media()
        return self._apply("hangup")

    def snapshot(self) -> dict:
        return {
            "contact": self.contact,
            "phase": self.phase,
            "media_allowed": self.media_allowed,
            "near": deepcopy(asdict(self.near)),
            "far": deepcopy(asdict(self.far)),
        }

    def _close_media(self) -> None:
        self.media_allowed = False
        for house in (self.near, self.far):
            house.screen_open = False
            house.camera_on = False
            house.mic_on = False

    def _apply(self, action: str) -> list[tuple[House, str]]:
        emitted: list[tuple[House, str]] = []
        for house, table in (("near", NEAR_EVENTS), ("far", FAR_EVENTS)):
            name = table[action]
            if not name:
                continue
            target = self.near if house == "near" else self.far
            target.event = name
            emitted.append((house, name))  # type: ignore[arg-type]
        return emitted
