import io
import json
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.request import urlopen

from jsonschema import Draft202012Validator, FormatChecker

from mapper.agent_body import main
from mapper.hal_client import dispatch, get_power
from mapper.map import map_event
from mapper.power import (
    VOLTAGE_RANGE,
    effective_low,
    map_power,
    simulate_power,
    soc_from_voltage,
    stamp_hal_origin,
    validate_power,
)
from mapper.serve import EventHandler, ThreadingHTTPServer
from mapper.skills import markers_for

ROOT = Path(__file__).resolve().parents[1]
POWER_SCHEMA = json.loads((ROOT / "protocol/power.schema.json").read_text())
EVENT_SCHEMA = json.loads((ROOT / "protocol/agent-body.schema.json").read_text())
POWER_VALIDATOR = Draft202012Validator(POWER_SCHEMA, format_checker=FormatChecker())
FORBIDDEN = ("password", "passwd", "credential", "/buddy/exec/type", "type_text")
GOLDEN = {
    "mains": ROOT / "fixtures/golden/power-mains.json",
    "battery-low": ROOT / "fixtures/golden/power-battery-low.json",
    "qi": ROOT / "fixtures/golden/power-qi.json",
}


class PowerSchemaTests(unittest.TestCase):
    def test_schema_accepts_golden_samples(self):
        for name, path in GOLDEN.items():
            with self.subTest(name=name):
                POWER_VALIDATOR.validate(json.loads(path.read_text())["sample"])

    def test_schema_rejects_unknown_fields_and_secrets(self):
        sample = json.loads(GOLDEN["mains"].read_text())["sample"]
        sample["password"] = "nope"
        with self.assertRaises(Exception):
            POWER_VALIDATOR.validate(sample)
        with self.assertRaises(ValueError):
            validate_power(sample)

    def test_schema_requires_origin(self):
        sample = json.loads(GOLDEN["mains"].read_text())["sample"]
        del sample["origin"]
        with self.assertRaises(Exception):
            POWER_VALIDATOR.validate(sample)

    def test_power_w_required_nullable(self):
        sample = json.loads(GOLDEN["mains"].read_text())["sample"]
        self.assertIn("power_w", sample)
        self.assertIsNone(sample["power_w"])
        POWER_VALIDATOR.validate(sample)
        validate_power(sample)
        missing = dict(sample)
        del missing["power_w"]
        with self.assertRaises(Exception):
            POWER_VALIDATOR.validate(missing)
        with self.assertRaises(ValueError) as ctx:
            validate_power(missing)
        self.assertIn("power_w", str(ctx.exception))
        sample["power_w"] = 0
        POWER_VALIDATOR.validate(sample)
        validate_power(sample)

    def test_agent_event_enum_stays_nine(self):
        events = EVENT_SCHEMA["properties"]["event"]["enum"]
        self.assertEqual(9, len(events))
        self.assertNotIn("power", events)
        self.assertNotIn("power_low", events)

    def test_no_tenth_event_golden(self):
        names = {path.name for path in (ROOT / "fixtures/golden").glob("*.markers.txt")}
        self.assertNotIn("power_low.markers.txt", names)
        self.assertNotIn("power.markers.txt", names)
        if names:
            self.assertEqual(9, len(names))

    def test_voltage_range_rejects_five_volt_mains(self):
        sample = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "mains", "origin": "sim",
            "power_w": None,
        }
        with self.assertRaises(ValueError) as ctx:
            validate_power(sample)
        self.assertIn("range", str(ctx.exception).lower())
        with self.assertRaises(Exception):
            POWER_VALIDATOR.validate(sample)
        self.assertEqual((11.0, 14.0), VOLTAGE_RANGE["mains"])
        self.assertEqual((9.0, 12.6), VOLTAGE_RANGE["battery"])
        self.assertEqual((4.5, 5.5), VOLTAGE_RANGE["qi"])

    def test_power_w_nullable_and_coil_miss(self):
        mains = json.loads(GOLDEN["mains"].read_text())["sample"]
        self.assertIsNone(mains["power_w"])
        POWER_VALIDATOR.validate(mains)
        qi = json.loads(GOLDEN["qi"].read_text())["sample"]
        self.assertIn(qi["power_w"], (5, 5.0, 10, 10.0))
        ten = dict(qi)
        ten["power_w"] = 10.0
        POWER_VALIDATOR.validate(ten)
        validate_power(ten)
        self.assertEqual((), map_power(ten).markers)
        coil_miss = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "qi", "origin": "sim",
            "soc_pct": None, "charging": False, "docked": True, "low": False,
            "power_w": 0,
        }
        POWER_VALIDATOR.validate(coil_miss)
        validate_power(coil_miss)
        self.assertEqual((), map_power(coil_miss).markers)
        self.assertTrue(coil_miss["docked"])
        self.assertFalse(coil_miss["charging"])


class PowerMapTests(unittest.TestCase):
    def test_golden_markers_are_exact_and_deterministic(self):
        for name, path in GOLDEN.items():
            with self.subTest(name=name):
                fixture = json.loads(path.read_text())
                first = list(map_power(fixture["sample"]).markers)
                second = list(map_power(fixture["sample"]).markers)
                self.assertEqual(fixture["markers"], first)
                self.assertEqual(first, second)

    def test_mains_emits_no_led(self):
        sample = json.loads(GOLDEN["mains"].read_text())["sample"]
        self.assertEqual((), map_power(sample).markers)

    def test_low_is_dim_solid_not_amber_and_never_aims(self):
        sample = json.loads(GOLDEN["battery-low"].read_text())["sample"]
        markers = list(map_power(sample).markers)
        blob = "".join(markers)
        self.assertIn("/led/solid", blob)
        self.assertIn("[48,16,0]", blob)
        self.assertNotIn("[255,150,0]", blob)
        self.assertNotIn("pulse", blob)
        self.assertNotIn("/servo", blob)
        self.assertNotIn("waiting_for_user", blob)

    def test_healthy_qi_emits_no_led(self):
        sample = json.loads(GOLDEN["qi"].read_text())["sample"]
        blob = "".join(map_power(sample).markers)
        self.assertEqual((), map_power(sample).markers)
        self.assertNotIn("[200,200,200]", blob)
        self.assertNotIn("breathing", blob)
        self.assertNotIn("[0,80,32]", blob)

    def test_healthy_usbc_docked_emits_no_led(self):
        sample = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 12.0, "source": "mains", "origin": "sim",
            "soc_pct": None, "charging": True, "docked": True, "low": False,
            "power_w": None,
        }
        blob = "".join(map_power(sample).markers)
        self.assertEqual((), map_power(sample).markers)
        self.assertNotIn("[0,200,80]", blob)
        self.assertNotIn("[0,80,32]", blob)

    def test_never_invents_power_hal_writes(self):
        for path in GOLDEN.values():
            blob = "".join(map_power(json.loads(path.read_text())["sample"]).markers)
            self.assertNotIn("[HW:/power", blob)
            self.assertNotIn("/sensing/power", blob)

    def test_help_rails_tokens_absent(self):
        for path in GOLDEN.values():
            rendered = json.dumps(map_power(json.loads(path.read_text())["sample"]).__dict__).lower()
            for token in FORBIDDEN:
                self.assertNotIn(token, rendered)

    def test_thinking_stays_blue_regardless_of_qi(self):
        qi = json.loads(GOLDEN["qi"].read_text())["sample"]
        output = map_event({"v": 1, "event": "thinking", "ts": "2026-08-25T15:00:00Z"}, power=qi)
        blob = "".join(output.markers)
        self.assertIn("[0,80,255]", blob)
        self.assertIn("breathing", blob)
        self.assertNotIn("[200,200,200]", blob)
        self.assertNotIn("[48,16,0]", blob)

    def test_thinking_stays_blue_on_low(self):
        low = json.loads(GOLDEN["battery-low"].read_text())["sample"]
        output = map_event({"v": 1, "event": "thinking", "ts": "2026-08-25T15:00:00Z"}, power=low)
        blob = "".join(output.markers)
        self.assertIn("[0,80,255]", blob)
        self.assertNotIn("[48,16,0]", blob)

    def test_completed_without_power_still_wiggles(self):
        output = map_event({"v": 1, "event": "completed", "ts": "2026-08-25T15:00:00Z"})
        blob = "".join(output.markers)
        self.assertIn("happy_wiggle", blob)

    def test_completed_on_qi_refuses_wiggle(self):
        qi = json.loads(GOLDEN["qi"].read_text())["sample"]
        output = map_event({"v": 1, "event": "completed", "ts": "2026-08-25T15:00:00Z"}, power=qi)
        blob = "".join(output.markers)
        self.assertNotIn("happy_wiggle", blob)
        self.assertNotIn("/servo/play", blob)
        self.assertIn("/led/effect", blob)

    def test_dance_on_qi_refuses_wiggle(self):
        qi = json.loads(GOLDEN["qi"].read_text())["sample"]
        markers = markers_for("dance", power=qi)
        blob = "".join(markers)
        self.assertNotIn("happy_wiggle", blob)
        self.assertNotIn("/servo/play", blob)
        self.assertEqual([], markers)
        self.assertEqual(['[HW:/servo/play:{"recording":"happy_wiggle"}]'], markers_for("dance"))


class PowerSimTests(unittest.TestCase):
    def test_sim_defaults_are_labeled_sim(self):
        mains = simulate_power("mains", ts="2026-08-25T15:00:00Z")
        self.assertEqual("sim", mains["origin"])
        self.assertEqual(12.0, mains["voltage_v"])
        self.assertIsNone(mains["power_w"])
        battery = simulate_power("battery", ts="2026-08-25T15:00:00Z")
        self.assertEqual("sim", battery["origin"])
        self.assertEqual(11.1, battery["voltage_v"])
        self.assertEqual(20, battery["soc_pct"])
        self.assertFalse(battery["low"])
        self.assertEqual((), map_power(battery).markers)
        qi = simulate_power("qi", ts="2026-08-25T15:00:00Z")
        self.assertEqual("sim", qi["origin"])
        self.assertEqual(5.0, qi["voltage_v"])
        self.assertIn(qi["power_w"], (5, 5.0, 10, 10.0))

    def test_sim_low_matches_battery_low_golden(self):
        sample = simulate_power("low", ts="2026-08-25T15:00:00Z")
        golden = json.loads(GOLDEN["battery-low"].read_text())
        self.assertEqual(golden["sample"], sample)
        self.assertEqual(golden["markers"], list(map_power(sample).markers))
        alias = simulate_power("battery-low", ts="2026-08-25T15:00:00Z")
        self.assertEqual(sample, alias)
        healthy = simulate_power("battery", ts="2026-08-25T15:00:00Z")
        self.assertEqual(11.1, healthy["voltage_v"])
        self.assertNotEqual(healthy["voltage_v"], sample["voltage_v"])

    def test_stamp_hal_keeps_live_voltage(self):
        live = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 13.8, "source": "mains", "charging": False, "docked": True, "low": False,
        }
        labeled = stamp_hal_origin(live)
        self.assertEqual("hal", labeled["origin"])
        self.assertEqual(13.8, labeled["voltage_v"])
        self.assertIsNone(labeled["power_w"])

    def test_qi_five_volts_is_not_low(self):
        self.assertFalse(effective_low(json.loads(GOLDEN["qi"].read_text())["sample"]))

    def test_battery_low_from_voltage_or_soc(self):
        self.assertTrue(effective_low({"source": "battery", "voltage_v": 10.2, "soc_pct": 20, "low": False}))
        self.assertTrue(effective_low({"source": "battery", "voltage_v": 11.1, "soc_pct": 10, "low": False}))
        self.assertFalse(effective_low({"source": "mains", "voltage_v": 12.0, "soc_pct": 10, "low": False}))
        self.assertFalse(effective_low({"source": "qi", "voltage_v": 5.0, "soc_pct": 10, "low": False}))

    def test_soc_table_is_deterministic(self):
        self.assertEqual(20, soc_from_voltage(11.1))
        self.assertEqual(soc_from_voltage(11.1), soc_from_voltage(11.1))


class PowerCliTests(unittest.TestCase):
    def test_sim_record_writes_origin_sim(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "power.json"
            self.assertEqual(0, main(["power", "--sim", "mains", "--record", str(record)]))
            payload = json.loads(record.read_text())
            self.assertEqual("sim", payload["origin"])
            self.assertEqual("sim", payload["sample"]["origin"])
            self.assertEqual([], payload["markers"])
            self.assertNotIn("dispatched", payload)

    def test_sim_qi_record_matches_golden_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "qi.json"
            self.assertEqual(0, main(["power", "--sim", "qi", "--record", str(record)]))
            payload = json.loads(record.read_text())
            self.assertEqual(json.loads(GOLDEN["qi"].read_text())["markers"], payload["markers"])
            self.assertEqual("sim", payload["sample"]["origin"])
            self.assertEqual([], payload["markers"])

    def test_sim_low_record_matches_golden(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "low.json"
            self.assertEqual(0, main(["power", "--sim", "low", "--record", str(record)]))
            payload = json.loads(record.read_text())
            golden = json.loads(GOLDEN["battery-low"].read_text())
            self.assertEqual(golden["markers"], payload["markers"])
            self.assertEqual("battery", payload["sample"]["source"])
            self.assertEqual(10.2, payload["sample"]["voltage_v"])
            self.assertTrue(payload["sample"]["low"])
            self.assertIn("[48,16,0]", "".join(payload["markers"]))

    def test_sim_battery_low_cli_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "low.json"
            self.assertEqual(0, main(["power", "--sim", "battery-low", "--record", str(record)]))
            payload = json.loads(record.read_text())
            golden = json.loads(GOLDEN["battery-low"].read_text())
            self.assertEqual(golden["markers"], payload["markers"])
            self.assertEqual(10.2, payload["sample"]["voltage_v"])
            self.assertNotEqual(11.1, payload["sample"]["voltage_v"])

    def test_skill_dance_on_qi_refuses_wiggle(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(0, main(["skill", "--name", "dance", "--sim", "qi"]))
        payload = json.loads(buf.getvalue())
        self.assertEqual([], payload["markers"])
        self.assertEqual("qi-cannot-dance", payload["reason"])
        self.assertNotIn("happy_wiggle", json.dumps(payload))

    def test_skill_hatch_on_qi_refuses_hop(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(0, main(["skill", "--name", "hatch", "--sim", "qi"]))
        payload = json.loads(buf.getvalue())
        self.assertEqual([], payload["markers"])
        self.assertEqual("qi-cannot-hatch", payload["reason"])
        self.assertNotIn("wake_up", json.dumps(payload))
        self.assertNotIn("/servo", json.dumps(payload.get("markers")))


class PowerClientTests(unittest.TestCase):
    def test_dispatch_refuses_power_writes(self):
        from mapper.hal_client import refuse_power_write
        with self.assertRaises(ValueError) as ctx:
            refuse_power_write("/power")
        self.assertIn("read telemetry", str(ctx.exception))
        with self.assertRaises(ValueError):
            refuse_power_write("/sensing/power")

    def test_hal_url_must_be_loopback(self):
        with self.assertRaises(ValueError):
            get_power("http://example.com:5001")
        with self.assertRaises(ValueError):
            dispatch(['[HW:/led/solid:{"color":[1,2,3],"transient":true}]'], "http://8.8.8.8:5001")

    def test_get_power_returns_none_on_404(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_error(404)

            def do_POST(self):
                self.send_error(599)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            self.assertIsNone(get_power(url))
        finally:
            server.shutdown()
            server.server_close()

    def test_get_power_is_get_not_post(self):
        methods = []
        sample = json.loads(GOLDEN["mains"].read_text())["sample"]
        sample["origin"] = "hal"
        sample["voltage_v"] = 12.4

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                methods.append(self.command)
                if self.path != "/power":
                    self.send_error(404)
                    return
                body = json.dumps(sample).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                methods.append(self.command)
                self.send_error(405)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            got = get_power(url)
            self.assertEqual(12.4, got["voltage_v"])
            self.assertEqual(["GET"], methods)
        finally:
            server.shutdown()
            server.server_close()

    def test_loopback_get_power_returns_latest_sample(self):
        EventHandler.latest_power = None
        EventHandler.hal_url = None
        server = ThreadingHTTPServer(("127.0.0.1", 0), EventHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            sample = json.loads(GOLDEN["qi"].read_text())["sample"]
            from urllib.request import Request
            request = Request(
                f"http://127.0.0.1:{port}/power",
                data=json.dumps(sample).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                posted = json.loads(response.read())
            self.assertEqual(json.loads(GOLDEN["qi"].read_text())["markers"], posted["markers"])
            with urlopen(f"http://127.0.0.1:{port}/power", timeout=2) as response:
                self.assertEqual(sample, json.loads(response.read()))
        finally:
            server.shutdown()
            server.server_close()
            EventHandler.latest_power = None

    def test_hal_404_falls_back_to_labeled_sim(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_error(404)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            with tempfile.TemporaryDirectory() as directory:
                record = Path(directory) / "out.json"
                self.assertEqual(0, main(["power", "--hal", url, "--sim", "battery", "--record", str(record)]))
                payload = json.loads(record.read_text())
                self.assertEqual("sim", payload["origin"])
                self.assertEqual("sim", payload["sample"]["origin"])
                self.assertEqual("hal_unavailable", payload["fallback"])
                self.assertEqual("battery", payload["sample"]["source"])
                self.assertEqual(11.1, payload["sample"]["voltage_v"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
