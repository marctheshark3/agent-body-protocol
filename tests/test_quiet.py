import unittest

from mapper.map import map_event
from mapper.policy import BodyPolicy

BASE = {"v": 1, "ts": "2026-08-21T18:00:00Z"}


class QuietPolicyTests(unittest.TestCase):
    def test_focus_and_night_never_speak(self):
        for mode in ("focus", "night"):
            for event in ("permission_required", "blocked", "tests_passed", "tests_failed", "completed"):
                with self.subTest(mode=mode, event=event):
                    output = map_event({**BASE, "event": event, "mode": mode})
                    self.assertIsNone(output.speech)

    def test_duplicate_event_is_coalesced_for_two_seconds(self):
        policy = BodyPolicy(clock=lambda: 100.0)
        event = {**BASE, "event": "thinking"}
        self.assertFalse(policy.apply(event).suppressed)
        self.assertTrue(policy.apply(event).suppressed)

    def test_completed_after_tests_passed_skips_second_flourish(self):
        times = iter((100.0, 103.0))
        policy = BodyPolicy(clock=lambda: next(times))
        policy.apply({**BASE, "event": "tests_passed"})
        result = policy.apply({**BASE, "event": "completed"})
        self.assertTrue(result.suppressed)


if __name__ == "__main__":
    unittest.main()
