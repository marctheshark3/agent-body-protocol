import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "protocol/agent-body.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
EVENTS = {
    "started", "thinking", "waiting_for_user", "permission_required", "blocked",
    "tests_passed", "tests_failed", "completed", "quiet",
}


class SchemaTests(unittest.TestCase):
    def test_schema_accepts_every_event(self):
        for event in EVENTS:
            with self.subTest(event=event):
                VALIDATOR.validate({"v": 1, "event": event, "ts": "2026-08-21T18:00:00Z"})

    def test_schema_rejects_unknown_event(self):
        with self.assertRaises(Exception):
            VALIDATOR.validate({"v": 1, "event": "vibing", "ts": "2026-08-21T18:00:00Z"})

    def test_schema_rejects_unknown_fields(self):
        with self.assertRaises(Exception):
            VALIDATOR.validate({"v": 1, "event": "quiet", "ts": "2026-08-21T18:00:00Z", "password": "nope"})

    def test_summary_is_bounded(self):
        with self.assertRaises(Exception):
            VALIDATOR.validate({"v": 1, "event": "blocked", "ts": "2026-08-21T18:00:00Z", "summary": "x" * 141})


if __name__ == "__main__":
    unittest.main()
