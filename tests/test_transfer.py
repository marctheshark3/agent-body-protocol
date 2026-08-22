import json
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from mapper.trajectory import record
from mapper.transfer import TransferError, replay, replay_row, scored_joints


def _hal(positions: dict, hex_color: str = "#002810"):
    state = {"positions": dict(positions), "hex": hex_color}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/led/color":
                payload = {"color": [0, 40, 16], "hex": state["hex"], "effect": None, "on": True}
            elif self.path == "/servo/position":
                payload = {"positions": state["positions"]}
            else:
                payload = {"media": "virtual"}
            raw = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(length)
            if self.path == "/servo/aim":
                state["positions"]["wrist_pitch.pos"] = -85.0
            raw = b'{"status":"ok"}'
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
    return server


class TransferTests(unittest.TestCase):
    def test_replay_measures_gap_and_refuses_raw_joints(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "src.jsonl"
            out = Path(directory) / "out.jsonl"
            record(
                src,
                house="pat",
                kind="aim",
                command={"direction": "user"},
                markers=['[HW:/servo/aim:{"direction":"user"}]'],
                dispatched=[],
                before={"ok": True, "positions": {"wrist_pitch.pos": 0.0}},
                after={
                    "ok": True,
                    "led": {"hex": "#002810"},
                    "positions": {
                        "base_yaw.pos": 0.0,
                        "base_pitch.pos": 0.0,
                        "elbow_pitch.pos": 0.0,
                        "wrist_pitch.pos": -85.0,
                        "wrist_roll.pos": 0.0,
                    },
                },
                source="unit",
            )
            server = _hal(
                {
                    "base_yaw.pos": 0.0,
                    "base_pitch.pos": 0.0,
                    "elbow_pitch.pos": 0.0,
                    "wrist_pitch.pos": 0.0,
                    "wrist_roll.pos": 0.0,
                }
            )
            try:
                report = replay(src, f"http://127.0.0.1:{server.server_address[1]}", out, "sam", settle_s=0)
            finally:
                server.shutdown()
                server.server_close()
            self.assertTrue(report["ok"])
            self.assertEqual(1, report["count"])
            self.assertLess(report["results"][0]["gap"]["max_joint_deg"], 5)

    def test_user_aim_does_not_score_parked_yaw(self):
        self.assertEqual(
            ("base_pitch.pos", "elbow_pitch.pos", "wrist_pitch.pos", "wrist_roll.pos"),
            scored_joints({
                "command": {"direction": "user"},
                "markers": ['[HW:/servo/aim:{"direction":"user"}]'],
            }),
        )
        self.assertEqual(
            ("base_yaw.pos",),
            scored_joints({
                "command": {"direction": "left"},
                "markers": ['[HW:/servo/aim:{"direction":"left"}]'],
            }),
        )
        self.assertEqual((), scored_joints({"markers": ['[HW:/led/solid:{"color":[0,200,80],"transient":true}]']}))

        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "led.jsonl"
            out = Path(directory) / "out.jsonl"
            record(
                src,
                house="pat",
                kind="event",
                command={"event": "thinking"},
                markers=['[HW:/led/effect:{"color":[0,80,255],"effect":"breathing","speed":0.3,"transient":true}]'],
                dispatched=[],
                before={"ok": True},
                after={"ok": True, "led": {"hex": "#0050ff"}, "positions": {}},
                source="unit",
            )
            server = _hal({"wrist_pitch.pos": 12.0}, hex_color="#112233")
            try:
                report = replay(src, f"http://127.0.0.1:{server.server_address[1]}", out, "sam", settle_s=0)
            finally:
                server.shutdown()
                server.server_close()
            self.assertFalse(report["ok"])
            self.assertFalse(report["results"][0]["gap"]["led_hex_match"])

        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "bare.jsonl"
            out = Path(directory) / "out.jsonl"
            record(
                src,
                house="pat",
                kind="aim",
                command={"direction": "user"},
                markers=['[HW:/servo/aim:{"direction":"user"}]'],
                dispatched=[],
                before={"ok": False, "error": "no_hal"},
                after={"ok": False, "error": "no_hal"},
                source="unit",
            )
            server = _hal({"wrist_pitch.pos": -85.0})
            try:
                report = replay(src, f"http://127.0.0.1:{server.server_address[1]}", out, "sam", settle_s=0)
            finally:
                server.shutdown()
                server.server_close()
            self.assertFalse(report["ok"])
            self.assertTrue(report["results"][0]["gap"]["missing_joints"])

        with self.assertRaises(TransferError):
            replay_row(
                {"markers": ["[HW:/servo/set:{}]"], "after": {}},
                "http://127.0.0.1:9",
                Path("/tmp/nope.jsonl"),
                "sam",
            )


if __name__ == "__main__":
    unittest.main()
