"""Stateful quiet, coalescing, and help-offer policy."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Callable, Mapping, Any

from .map import BodyOutput, map_event


@dataclass(frozen=True)
class PolicyResult:
    output: BodyOutput
    suppressed: bool = False
    reason: str | None = None


class BodyPolicy:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._last_event: str | None = None
        self._last_event_at = float("-inf")
        self._tests_passed_at = float("-inf")
        self._last_help_offer_at = float("-inf")

    def apply(self, event: Mapping[str, Any]) -> PolicyResult:
        now = self._clock()
        name = str(event["event"])
        output = map_event(event)

        if name == self._last_event and now - self._last_event_at < 2.0:
            return PolicyResult(BodyOutput(()), True, "duplicate-within-2s")

        self._last_event = name
        self._last_event_at = now

        if name == "completed" and now - self._tests_passed_at < 5.0:
            return PolicyResult(BodyOutput(()), True, "completed-after-tests-passed")

        if name == "tests_passed":
            self._tests_passed_at = now

        if name == "blocked" and output.speech:
            if now - self._last_help_offer_at < 900.0:
                output = replace(output, speech=None)
            else:
                self._last_help_offer_at = now

        return PolicyResult(output)
