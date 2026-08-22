import json
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from mapper.trajectory import SCHEMA, load_rows, read_body, record


class TrajectoryTests(unittest.TestCase):
    def test_record_appends_schema_and_no_raw_joint_command(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "traj.jsonl"
            row = record(
                path,
                house="pat",
                kind="aim",
                command={"direction": "user"},
                markers=['[HW:/servo/aim:{"direction":"user"}]'],
                dispatched=[{"path": "/servo/aim", "status": 200}],
                before={"ok": True, "positions": {"wrist_pitch.pos": 0}},
                after={"ok": True, "positions": {"wrist_pitch.pos": -85}},
                source="unit",
            )
            self.assertEqual(SCHEMA, row["schema"])
            self.assertNotIn("wrist_pitch", json.dumps(row["command"]))
            loaded = load_rows(path)
            self.assertEqual(1, len(loaded))
            self.assertEqual("user", loaded[0]["command"]["direction"])

    def test_read_body_uses_led_and_servo_not_sim_media_only(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = {
                    "/led/color": {"color": [0, 40, 16], "hex": "#002810", "effect": None, "on": True},
                    "/servo/position": {"positions": {"wrist_pitch.pos": -85.0, "base_yaw.pos": 0.0}},
                    "/simulator/state": {"media": "virtual"},
                }[self.path]
                raw = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = read_body(f"http://127.0.0.1:{server.server_address[1]}")
        finally:
            server.shutdown()
            server.server_close()
        self.assertTrue(body["ok"])
        self.assertEqual([0, 40, 16], body["led"]["color"])
        self.assertEqual(-85.0, body["positions"]["wrist_pitch.pos"])
        self.assertEqual("virtual", body["simulator"]["media"])


if __name__ == "__main__":
    unittest.main()
