import json
import tempfile
import unittest
from pathlib import Path

from mapper.agent_body import main
from mapper.hal_client import parse_marker


class CliTests(unittest.TestCase):
    def test_post_record_writes_evidence_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "out.json"
            self.assertEqual(0, main(["post", "--event", "thinking", "--record", str(record)]))
            payload = json.loads(record.read_text())
            self.assertEqual("thinking", payload["event"]["event"])
            self.assertTrue(payload["markers"])
            self.assertNotIn("dispatched", payload)

    def test_parse_marker_handles_rgb_array(self):
        path, payload = parse_marker('[HW:/led/solid:{"color":[1,2,3],"transient":true}]')
        self.assertEqual("/led/solid", path)
        self.assertEqual([1, 2, 3], payload["color"])


if __name__ == "__main__":
    unittest.main()
