import unittest
from pathlib import Path

from mapper.map import map_event

ROOT = Path(__file__).resolve().parents[1]
EVENTS = (
    "started", "thinking", "waiting_for_user", "permission_required", "blocked",
    "tests_passed", "tests_failed", "completed", "quiet",
)


class GoldenMapTests(unittest.TestCase):
    def test_all_events_match_exact_golden_marker_sequences(self):
        for event in EVENTS:
            with self.subTest(event=event):
                expected = (ROOT / f"fixtures/golden/{event}.markers.txt").read_text().rstrip("\n")
                actual = "".join(map_event({"v": 1, "event": event, "ts": "2026-08-21T18:00:00Z"}).markers)
                self.assertEqual(expected, actual)

    def test_no_mapping_drives_raw_pitch(self):
        for event in EVENTS:
            output = map_event({"v": 1, "event": event, "ts": "2026-08-21T18:00:00Z"})
            self.assertNotIn('"pitch"', "".join(output.markers))

    def test_led_writes_are_transient(self):
        for event in EVENTS:
            for marker in map_event({"v": 1, "event": event, "ts": "2026-08-21T18:00:00Z"}).markers:
                if marker.startswith("[HW:/led/solid:") or marker.startswith("[HW:/led/effect:"):
                    self.assertIn('"transient":true', marker)


if __name__ == "__main__":
    unittest.main()
