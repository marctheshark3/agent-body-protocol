import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from mapper.proof import grade, joint_deltas, run_proof


class _Hal(BaseHTTPRequestHandler):
    positions = {"base_yaw.pos": 0.0, "base_pitch.pos": -20.0, "elbow_pitch.pos": 32.0, "wrist_pitch.pos": 0.0, "wrist_roll.pos": 0.0}
    color = [0, 0, 0]
    hex_color = "#000000"

    def log_message(self, format, *args):
        return

    def _send(self, payload, code=200):
        raw = __import__("json").dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/led/color":
            self._send({"color": self.color, "hex": self.hex_color, "on": any(self.color), "effect": None})
            return
        if self.path == "/servo/position":
            self._send({"positions": dict(type(self).positions)})
            return
        self._send({}, 404)

    def do_POST(self):
        if self.path == "/servo/aim":
            type(self).positions["wrist_pitch.pos"] = -85.0
            self._send({"status": "ok"})
            return
        if self.path == "/servo/track":
            self.send_response(500)
            self.end_headers()
            return
        self._send({"status": "ok"})


class ProofTests(unittest.TestCase):
    def test_missing_joints_are_zero_not_success(self):
        self.assertEqual(0.0, joint_deltas({"positions": {}}, {"positions": {}})["wrist_pitch.pos"])

    def test_follow_500_is_the_honest_pass(self):
        row = {"kind": "follow", "dispatched": [{"path": "/servo/track", "status": 500}], "deltas": {}, "led_before": "#000", "led_after": "#000"}
        self.assertTrue(grade(row)["ok"])

    def test_look_against_mock_hal_moves_wrist(self):
        server = HTTPServer(("127.0.0.1", 0), _Hal)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            report = run_proof("look", f"http://127.0.0.1:{server.server_address[1]}", settle_s=0)
        finally:
            server.shutdown()
            server.server_close()
        self.assertGreaterEqual(report["deltas"]["wrist_pitch.pos"], 5)
        self.assertTrue(report["grade"]["ok"])
        self.assertEqual(200, report["dispatched"][0]["status"])


if __name__ == "__main__":
    unittest.main()
