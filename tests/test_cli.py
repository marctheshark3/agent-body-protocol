import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from mapper.agent_body import main
from mapper.hal_client import parse_marker
from mapper.serve import EventHandler, ThreadingHTTPServer, validate_event


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

    def test_server_rejects_unknown_fields(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), EventHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=2)
            body = json.dumps({
                "v": 1,
                "event": "thinking",
                "ts": "2026-08-21T18:00:00Z",
                "password": "nope",
            })
            connection.request("POST", "/event", body=body, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            self.assertEqual(400, response.status)
            self.assertIn("unknown fields", response.read().decode())
        finally:
            server.shutdown()
            server.server_close()

    def test_server_rejects_non_object_payload(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), EventHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=2)
            connection.request("POST", "/event", body="[]", headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            self.assertEqual(400, response.status)
            self.assertIn("JSON object", response.read().decode())
        finally:
            server.shutdown()
            server.server_close()

    def test_aim_log_without_hal_still_writes_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "traj.jsonl"
            self.assertEqual(0, main(["aim", "--direction", "user", "--log", str(log)]))
            row = json.loads(log.read_text().splitlines()[0])
            self.assertEqual("abp.trajectory/v1", row["schema"])
            self.assertEqual("aim", row["kind"])
            self.assertEqual("user", row["command"]["direction"])
            self.assertEqual("no_hal", row["before"]["error"])
            self.assertNotIn("wrist_pitch", json.dumps(row["command"]))

    def test_skill_dance_is_stock_play(self):
        with tempfile.TemporaryDirectory() as directory:
            # stdout only; no HAL
            self.assertEqual(0, main(["skill", "--name", "dance"]))

    def test_aim_record_is_named_only(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "aim.json"
            self.assertEqual(0, main(["aim", "--direction", "user", "--record", str(record)]))
            payload = json.loads(record.read_text())
            self.assertEqual(['[HW:/servo/aim:{"direction":"user"}]'], payload["markers"])
            self.assertNotIn("base_yaw", record.read_text())

    def test_validate_event_rejects_invalid_mode(self):
        with self.assertRaises(ValueError):
            validate_event({
                "v": 1,
                "event": "permission_required",
                "ts": "2026-08-21T18:00:00Z",
                "mode": "party",
            })


if __name__ == "__main__":
    unittest.main()
