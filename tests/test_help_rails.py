import json
import unittest
from pathlib import Path

from mapper.map import map_event
from mapper.policy import BodyPolicy

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("password", "passwd", "credential", "/buddy/exec/type", "type_text")


class HelpRailsTests(unittest.TestCase):
    def test_blocked_never_emits_secret_or_typing_actions(self):
        event = {
            "v": 1,
            "event": "blocked",
            "ts": "2026-08-21T18:00:00Z",
            "consent": "yes",
            "detail": "The visible screen contains a password field",
        }
        rendered = json.dumps(map_event(event).__dict__).lower()
        for forbidden in FORBIDDEN:
            self.assertNotIn(forbidden, rendered)

    def test_consent_off_silences_help_offer(self):
        output = map_event({"v": 1, "event": "blocked", "ts": "2026-08-21T18:00:00Z", "consent": "off"})
        self.assertIsNone(output.speech)

    def test_help_offer_has_fifteen_minute_cooldown(self):
        times = iter((100.0, 101.0, 1001.0))
        policy = BodyPolicy(clock=lambda: next(times))
        event = {"v": 1, "event": "blocked", "ts": "2026-08-21T18:00:00Z", "consent": "ask"}
        self.assertEqual("Want help with that?", policy.apply(event).output.speech)
        self.assertIsNone(policy.apply(event).output.speech)
        self.assertEqual("Want help with that?", policy.apply(event).output.speech)

    def test_synthetic_fixture_contains_no_pii(self):
        fixture = (ROOT / "fixtures/screens/forgot-password.txt").read_text().lower()
        self.assertIn("synthetic", fixture)
        self.assertNotIn("@", fixture)


if __name__ == "__main__":
    unittest.main()
