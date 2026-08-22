"""Consent-gated Help Mode on blocked. Never types secrets."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass

HELP_EVENTS = {
    "stuck": "blocked",
    "consent_yes": "thinking",
    "point_reset": "waiting_for_user",
    "done": "completed",
    "refuse": "quiet",
}

FORBIDDEN = ("password", "passwd", "credential", "otp", "ssn")
SCREEN = [
    "Forgot password?",
    "[ Email address ]",
    "[ Send reset link ]",
]


@dataclass
class HelpMode:
    phase: str = "idle"
    consented: bool = False
    pointed: str | None = None
    speech: str | None = None

    def reset(self) -> None:
        self.phase = "idle"
        self.consented = False
        self.pointed = None
        self.speech = None

    def stuck(self) -> str:
        self.phase = "offer"
        self.consented = False
        self.speech = "Want help with that?"
        return HELP_EVENTS["stuck"]

    def consent_yes(self) -> str:
        if self.phase != "offer":
            raise ValueError("nothing to consent")
        self.phase = "guiding"
        self.consented = True
        self.speech = "Tap Send reset link. I will not type the secret."
        return HELP_EVENTS["consent_yes"]

    def refuse(self) -> str:
        self.reset()
        self.phase = "idle"
        self.speech = None
        return HELP_EVENTS["refuse"]

    def point_reset(self) -> str:
        if not self.consented:
            raise ValueError("help requires consent")
        self.phase = "pointing"
        self.pointed = "Send reset link"
        self.speech = "That control is not a password field."
        return HELP_EVENTS["point_reset"]

    def done(self) -> str:
        if self.phase not in {"pointing", "guiding"}:
            raise ValueError("help is not in progress")
        event = HELP_EVENTS["done"]
        self.reset()
        return event

    def snapshot(self) -> dict:
        return {
            **deepcopy(asdict(self)),
            "screen": list(SCREEN),
            "never": list(FORBIDDEN),
        }
