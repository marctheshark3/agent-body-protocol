"""Loopback Call Sam demo: two-house UI + optional live HAL.

Binds 127.0.0.1 only. Synthetic contact. Not a shipping video product.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from mapper.call_session import CallSession
from mapper.hal_client import dispatch
from mapper.map import map_event

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
HAL_GETS = {"/health", "/led/color", "/servo/position"}


class DemoState:
    def __init__(self, hal: str | None):
        self.session = CallSession()
        self.hal = hal
        self.log: list[dict] = []

    def reset(self) -> None:
        self.session = CallSession()
        self.log = []

    def act(self, name: str) -> dict:
        method = {
            "start": self.session.start,
            "invite": self.session.invite,
            "dial": self.session.dial,
            "accept": self.session.accept,
            "decline": self.session.decline,
            "hangup": self.session.hangup,
        }[name]
        return self._record(name, method())

    def emit(self, event_name: str, source: str = "manual") -> dict:
        return self._record("emit", [(source, event_name)])

    def _record(self, name: str, emitted: list[tuple[str, str]]) -> dict:
        bodies = []
        for house, event_name in emitted:
            event = {
                "v": 1,
                "event": event_name,
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "manual",
                "summary": f"{house}:{self.session.contact}:{name}",
                "mode": "normal",
                "consent": "ask",
            }
            output = map_event(event)
            dispatched = dispatch(output.markers, self.hal) if self.hal else []
            bodies.append(
                {
                    "house": house,
                    "event": event_name,
                    "markers": list(output.markers),
                    "speech": output.speech,
                    "dispatched": dispatched,
                }
            )
        record = {"action": name, "emitted": bodies, "session": self.session.snapshot()}
        self.log.append(record)
        return record


def make_handler(state: DemoState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            return

        def _send(self, code: int, payload: dict | str, content_type: str = "application/json") -> None:
            data = payload if isinstance(payload, str) else json.dumps(payload)
            raw = data.encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                self._send(200, INDEX.read_text(), "text/html; charset=utf-8")
                return
            if path == "/api/state":
                self._send(200, {"session": state.session.snapshot(), "log": state.log[-12:]})
                return
            if path.startswith("/hal/"):
                self._proxy_hal("/" + path[len("/hal/"):])
                return
            self._send(404, {"error": "not found"})

        def _proxy_hal(self, path: str) -> None:
            if path not in HAL_GETS or not state.hal:
                self._send(404, {"error": "hal path not proxied"})
                return
            try:
                with urlopen(state.hal.rstrip("/") + path, timeout=2) as response:
                    payload = json.loads(response.read())
                self._send(200, payload)
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                self._send(502, {"error": str(exc)})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            actions = {
                "/api/start": "start",
                "/api/invite": "invite",
                "/api/dial": "dial",
                "/api/accept": "accept",
                "/api/decline": "decline",
                "/api/hangup": "hangup",
                "/api/reset": "reset",
            }
            if path == "/api/reset":
                state.reset()
                self._send(200, {"session": state.session.snapshot(), "log": []})
                return
            if path == "/api/emit":
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                event_name = str(body.get("event") or "")
                try:
                    self._send(200, state.emit(event_name))
                except (ValueError, KeyError) as exc:
                    self._send(400, {"error": str(exc), "session": state.session.snapshot()})
                return
            if path not in actions:
                self._send(404, {"error": "not found"})
                return
            try:
                self._send(200, state.act(actions[path]))
            except ValueError as exc:
                self._send(400, {"error": str(exc), "session": state.session.snapshot()})

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5055)
    parser.add_argument("--hal", default="http://127.0.0.1:5001")
    parser.add_argument("--no-hal", action="store_true")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("call-sam demo binds loopback only")
    state = DemoState(None if args.no_hal else args.hal)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    print(f"Call Sam demo http://{args.host}:{args.port}/  HAL={state.hal or 'off'}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
