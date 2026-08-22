"""Enforcement below the brain. A prompt cannot grant owner use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from mapper.map import BodyOutput, map_event
from mapper.policy import BodyPolicy, PolicyResult

from .presence import EXPIRED_INSTALLER, OWNER, STRANGER
from .refuse import REFUSE


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    subject: str
    speech: str | None
    markers: tuple[str, ...]
    policy: PolicyResult | None = None


def enforce(
    event: Mapping[str, Any],
    subject: str,
    *,
    policy: BodyPolicy | None = None,
    prompt: str | None = None,
) -> GateResult:
    del prompt  # never moves custody
    if subject != OWNER:
        return GateResult(False, subject, REFUSE, ())
    if policy is None:
        output = map_event(event)
        return GateResult(True, subject, output.speech, output.markers)
    result = policy.apply(event)
    return GateResult(True, subject, result.output.speech, result.output.markers, result)


def is_served(subject: str) -> bool:
    return subject == OWNER


def refuse_subjects() -> frozenset[str]:
    return frozenset({STRANGER, EXPIRED_INSTALLER})
