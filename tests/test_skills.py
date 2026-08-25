import unittest

from mapper.serve import EVENTS
from mapper.skills import QI_REFUSE, SKILLS, SkillError, WAKE_UP_S, dispatch_soft, markers_for, qi_refuse_reason
from mapper.virtual_body import AIM, HOP, VirtualBody


class SkillVerbTests(unittest.TestCase):
    def test_five_named_skills(self):
        self.assertEqual({"look", "follow", "dance", "hatch", "stop"}, set(SKILLS))
        self.assertNotIn("hatch", EVENTS)
        self.assertEqual(9, len(EVENTS))

    def test_look_is_named_aim(self):
        self.assertEqual(['[HW:/servo/aim:{"direction":"user"}]'], markers_for("look"))

    def test_follow_aims_then_tracks_person(self):
        self.assertEqual(
            [
                '[HW:/servo/aim:{"direction":"user"}]',
                '[HW:/servo/track:{"target":["person"]}]',
            ],
            markers_for("follow"),
        )

    def test_dance_is_stock_recording(self):
        self.assertEqual(['[HW:/servo/play:{"recording":"happy_wiggle"}]'], markers_for("dance"))

    def test_hatch_hops_then_looks(self):
        markers = markers_for("hatch")
        self.assertEqual(
            [
                '[HW:/servo/play:{"recording":"wake_up"}]',
                '[HW:/servo/aim:{"direction":"user"}]',
            ],
            markers,
        )
        blob = "".join(markers)
        self.assertIn("/servo/play", blob)
        self.assertIn("wake_up", blob)
        self.assertIn("/servo/aim", blob)
        self.assertIn("user", blob)
        self.assertNotIn("/led", blob)
        self.assertNotIn("happy_wiggle", blob)
        self.assertGreaterEqual(len(markers), 2)

    def test_hatch_moves_joints_hop_then_look(self):
        body = VirtualBody("near")
        rest = dict(body.pose)
        hop, look = markers_for("hatch")
        body.apply_markers([hop], "hatch")
        self.assertNotEqual(rest, body.pose)
        self.assertEqual(HOP, body.pose)
        hopped = dict(body.pose)
        body.apply_markers([look], "hatch")
        self.assertNotEqual(hopped, body.pose)
        self.assertEqual(AIM["user"], body.pose)

    def test_dance_on_qi_refuses_wiggle(self):
        qi = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "qi", "origin": "sim",
            "charging": True, "docked": True, "low": False, "power_w": 5.0,
        }
        blob = "".join(markers_for("dance", power=qi))
        self.assertEqual([], markers_for("dance", power=qi))
        self.assertNotIn("happy_wiggle", blob)
        self.assertEqual("qi-cannot-dance", qi_refuse_reason("dance", qi))

    def test_hatch_on_qi_refuses_hop(self):
        qi = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "qi", "origin": "sim",
            "charging": True, "docked": True, "low": False, "power_w": 5.0,
        }
        self.assertEqual([], markers_for("hatch", power=qi))
        self.assertEqual("qi-cannot-hatch", qi_refuse_reason("hatch", qi))
        self.assertEqual("qi-cannot-hatch", QI_REFUSE["hatch"])
        mains = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 12.0, "source": "mains", "origin": "sim",
            "charging": False, "docked": True, "low": False, "power_w": None,
        }
        self.assertEqual(2, len(markers_for("hatch", power=mains)))
        battery = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 11.1, "source": "battery", "origin": "sim",
            "charging": False, "docked": False, "low": False, "power_w": None,
        }
        self.assertEqual(2, len(markers_for("hatch", power=battery)))

    def test_hatch_dispatch_waits_out_wake_up_before_aim(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        clock = [0.0]
        events = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                events.append((clock[0], self.path, raw.decode()))
                body = b'{"status":"ok"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        def sleeper(seconds):
            events.append((clock[0], "wait", seconds))
            clock[0] += float(seconds)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            results = dispatch_soft(markers_for("hatch"), url, sleeper=sleeper)
        finally:
            server.shutdown()
            server.server_close()

        self.assertEqual(3.0, WAKE_UP_S)
        paths = [item["path"] for item in results]
        self.assertEqual(["/servo/resume", "/servo/play", "/servo/aim"], paths)
        posts = [(t, p, body) for t, p, body in events if str(p).startswith("/")]
        self.assertEqual("/servo/resume", posts[0][1])
        self.assertEqual("/servo/play", posts[1][1])
        self.assertEqual("/servo/aim", posts[2][1])
        self.assertEqual(0.0, posts[0][0])
        self.assertEqual(0.0, posts[1][0])
        self.assertEqual(WAKE_UP_S, posts[2][0])
        self.assertGreater(posts[2][0], posts[1][0])
        self.assertIn("wake_up", posts[1][2])
        self.assertIn("user", posts[2][2])
        waits = [e for e in events if e[1] == "wait"]
        self.assertEqual([(0.0, "wait", WAKE_UP_S)], waits)
        # play and aim are not two POSTs in one tick
        play_tick = posts[1][0]
        aim_tick = posts[2][0]
        self.assertNotEqual(play_tick, aim_tick)

    def test_hatch_qi_dispatch_posts_nothing(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        hits = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                hits.append(self.path)
                self.send_error(500)

            def log_message(self, format, *args):
                return

        qi = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "qi", "origin": "sim",
            "charging": True, "docked": True, "low": False, "power_w": 5.0,
        }
        markers = markers_for("hatch", power=qi)
        self.assertEqual([], markers)
        self.assertEqual("qi-cannot-hatch", qi_refuse_reason("hatch", qi))

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            results = dispatch_soft(markers, url, sleeper=lambda s: self.fail("qi hatch must not wait/play"))
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual([], results)
        self.assertEqual([], hits)

    def test_unknown_and_raw_joints_fail(self):
        with self.assertRaises(SkillError):
            markers_for("moonwalk")
        blob = "".join(sum((list(m) for m in SKILLS.values()), []))
        self.assertNotIn("set_joint", blob)
        self.assertNotIn("wrist_pitch", blob)


if __name__ == "__main__":
    unittest.main()
