import unittest

from mapper.hal_client import dispatch, get_power, refuse_power_write
from mapper.skills import dispatch_soft
from mapper.trajectory import read_body


class HalLoopbackPinTests(unittest.TestCase):
    def test_dispatch_soft_pins_loopback_and_refuses_power_write(self):
        led = '[HW:/led/solid:{"color":[1,2,3],"transient":true}]'
        with self.assertRaises(ValueError):
            dispatch_soft([led], "http://8.8.8.8:5001")
        with self.assertRaises(ValueError):
            dispatch_soft(['[HW:/power:{"voltage_v":12}]'], "http://127.0.0.1:5001")
        with self.assertRaises(ValueError):
            read_body("http://example.com:5001")
        with self.assertRaises(ValueError):
            get_power("http://example.com:5001")
        with self.assertRaises(ValueError):
            dispatch([led], "http://8.8.8.8:5001")
        with self.assertRaises(ValueError):
            refuse_power_write("/power")

    def test_get_power_continues_past_unusable_power_path(self):
        import json
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/power":
                    body = b"not-json"
                elif self.path == "/sensing/power":
                    body = json.dumps({"voltage_v": 12.4, "source": "mains"}).encode()
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            got = get_power(url)
            self.assertEqual(12.4, got["voltage_v"])
            self.assertEqual("mains", got["source"])
        finally:
            server.shutdown()
            server.server_close()

    def test_get_power_empty_object_falls_through_then_none(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/power":
                    body = b"{}"
                elif self.path == "/sensing/power":
                    body = b"[]"
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertIsNone(get_power(f"http://127.0.0.1:{server.server_address[1]}"))
        finally:
            server.shutdown()
            server.server_close()
