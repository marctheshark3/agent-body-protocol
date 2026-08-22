"""Consented two-house call mapped onto the nine ABP events.

This is a skill, not a tenth event. Video and raw audio never ride these events.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Literal

House = Literal["near", "far"]
Phase = Literal["idle", "confirm", "ringing", "in_call", "ended", "missed"]

# Public fixtures use synthetic names only.
CONTACT = "Sam"
MAX_NOTE = 140

NEAR_EVENTS = {
    "confirm": "permission_required",
    "ringing": "waiting_for_user",
    "accept": "quiet",
    "decline": "quiet",
    "hangup": "quiet",
    "no_answer": "waiting_for_user",
    "leave_message": "completed",
}
FAR_EVENTS = {
    "confirm": None,
    "ringing": "permission_required",
    "accept": "quiet",
    "decline": "quiet",
    "hangup": "quiet",
    "no_answer": "quiet",
    "leave_message": "waiting_for_user",
}


def sanitize_note(text: str) -> str:
    note = " ".join(str(text or "").split())
    lowered = note.lower()
    if any(token in lowered for token in ("password", "passwd", "otp", "ssn", "recovery code")):
        raise ValueError("message rejected: looks like a secret")
    if len(note) > MAX_NOTE:
        note = note[:MAX_NOTE].rstrip()
    if not note:
        raise ValueError("empty message")
    return note


@dataclass
class HouseState:
    house: House
    event: str | None = None
    screen_open: bool = False
    camera_on: bool = False
    mic_on: bool = False
    heard: str | None = None
    message: str | None = None


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
        if self.phase in {"ended", "missed"}:
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
        if self.phase in {"idle", "ended", "missed"}:
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
        self.near.mic_on = False
        self.far.mic_on = False
        return self._apply("hangup")

    def no_answer(self) -> list[tuple[House, str]]:
        if self.phase != "ringing":
            raise ValueError("no-answer requires a ring")
        self.phase = "missed"
        self._close_media()
        return self._apply("no_answer")

    def leave_message(self, text: str) -> list[tuple[House, str]]:
        if self.phase not in {"ringing", "missed"}:
            raise ValueError("leave-message requires a missed or ringing call")
        note = sanitize_note(text)
        if self.phase == "ringing":
            self._apply("no_answer")
        self.phase = "missed"
        self.far.message = note
        self.far.screen_open = True
        self.near.mic_on = False
        return self._apply("leave_message")

    def talk(self, text: str, speaker: House = "near") -> None:
        if self.phase != "in_call" or not self.media_allowed:
            raise ValueError("talk requires an accepted call")
        note = sanitize_note(text)
        source = self.near if speaker == "near" else self.far
        other = self.far if speaker == "near" else self.near
        source.mic_on = True
        other.heard = note
        other.screen_open = True

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
