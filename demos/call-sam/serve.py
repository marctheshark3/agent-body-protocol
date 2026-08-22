"""Loopback use-case demo: two lamps, help mode, nine events.

Binds 127.0.0.1 only. Synthetic contact. Audio never leaves the browser except
as a short sanitized transcript posted to /api/talk or /api/message.
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
from mapper.help_mode import HelpMode
from mapper.map import map_event
from mapper.proof import run_proof
from mapper.skills import dispatch_soft, markers_for
from mapper.virtual_body import VirtualBody

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
PROOF = ROOT / "proof.html"
HAL_GETS = {"/health", "/led/color", "/servo/position"}
SCENARIOS = {
    "ci_pass": [("near", "started"), ("near", "thinking"), ("near", "tests_passed"), ("near", "completed")],
    "ci_fail": [("near", "started"), ("near", "thinking"), ("near", "tests_failed")],
    "rubber_duck": [("near", "started"), ("near", "thinking"), ("near", "permission_required")],
    "night_think": [("near", "thinking")],
}


class DemoState:
    def __init__(self, hal: str | None, far_hal: str | None = None):
        self.session = CallSession()
        self.help = HelpMode()
        self.hal = hal
        self.far_hal = far_hal
        self.log: list[dict] = []
        self.near_body = VirtualBody("near")
        self.far_body = VirtualBody("far")

    def reset(self) -> None:
        self.session = CallSession()
        self.help = HelpMode()
        self.log = []
        self.near_body.reset()
        self.far_body.reset()

    def snapshot(self) -> dict:
        return {
            "session": self.session.snapshot(),
            "help": self.help.snapshot(),
            "near_body": self.near_body.snapshot(),
            "far_body": self.far_body.snapshot(),
            "near_hal": self.hal,
            "far_hal": self.far_hal,
            "log": self.log[-12:],
            "uses": [
                "nine_events",
                "ci_sentinel",
                "rubber_duck",
                "help_mode",
                "two_lamp_call",
                "no_answer_message",
                "in_call_talk_on_screen",
                "look_follow_dance_stop",
            ],
        }

    def skill(self, name: str, house: str = "near") -> dict:
        markers = markers_for(name)
        target = self.far_hal if house == "far" else self.hal
        dispatched = dispatch_soft(markers, target) if target else []
        body = self.far_body if house == "far" else self.near_body
        body.apply_markers(markers, name)
        record = {
            "action": f"skill_{name}",
            "skill": name,
            "house": "far" if house == "far" else "near",
            "markers": markers,
            "dispatched": dispatched,
            "session": self.session.snapshot(),
            "near_body": self.near_body.snapshot(),
            "far_body": self.far_body.snapshot(),
            "help": self.help.snapshot(),
            "note": (
                "follow needs a camera; HAL_SIMULATE often 500s on /servo/track. "
                "dance/look/stop use stock HAL verbs."
            ),
        }
        self.log.append(record)
        return record

    def proof(self, name: str, house: str = "near") -> dict:
        target = self.far_hal if house == "far" else self.hal
        row = run_proof(name, target)
        if name in {"look", "follow", "dance", "stop"}:
            body = self.far_body if house == "far" else self.near_body
            body.apply_markers(row.get("markers") or [], name)
        row["near_body"] = self.near_body.snapshot()
        row["far_body"] = self.far_body.snapshot()
        self.log.append(row)
        return row

    def act(self, name: str) -> dict:
        method = {
            "start": self.session.start,
            "invite": self.session.invite,
            "dial": self.session.dial,
            "accept": self.session.accept,
            "decline": self.session.decline,
            "hangup": self.session.hangup,
            "no_answer": self.session.no_answer,
        }[name]
        return self._record(name, method())

    def leave_message(self, text: str) -> dict:
        return self._record("leave_message", self.session.leave_message(text))

    def talk(self, text: str, speaker: str = "near") -> dict:
        house = "far" if speaker == "far" else "near"
        self.session.talk(text, house)
        record = {
            "action": "talk",
            "emitted": [],
            "session": self.session.snapshot(),
            "near_body": self.near_body.snapshot(),
            "far_body": self.far_body.snapshot(),
            "help": self.help.snapshot(),
        }
        self.log.append(record)
        return record

    def emit(self, event_name: str, house: str = "near") -> dict:
        target = "far" if house == "far" else "near"
        return self._record("emit", [(target, event_name)])

    def scenario(self, name: str) -> dict:
        if name == "help":
            return self.help_act("stuck")
        if name not in SCENARIOS:
            raise ValueError(f"unknown scenario {name}")
        return self._record(name, list(SCENARIOS[name]))

    def help_act(self, name: str) -> dict:
        method = {
            "stuck": self.help.stuck,
            "consent_yes": self.help.consent_yes,
            "point_reset": self.help.point_reset,
            "done": self.help.done,
            "refuse": self.help.refuse,
        }[name]
        event_name = method()
        return self._record(f"help_{name}", [("near", event_name)])

    def _record(self, name: str, emitted: list[tuple[str, str]]) -> dict:
        bodies = []
        for house, event_name in emitted:
            event = {
                "v": 1,
                "event": event_name,
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "manual",
                "summary": f"{house}:{self.session.contact}:{name}",
                "mode": "night" if name == "night_think" else "normal",
                "consent": "ask",
            }
            output = map_event(event)
            body = self.far_body if house == "far" else self.near_body
            body.apply(event_name)
            target = self.far_hal if house == "far" else self.hal
            dispatched = dispatch(output.markers, target) if target else []
            bodies.append(
                {
                    "house": house,
                    "event": event_name,
                    "markers": list(output.markers),
                    "speech": output.speech,
                    "dispatched": dispatched,
                    "body": body.snapshot(),
                }
            )
        record = {
            "action": name,
            "emitted": bodies,
            "session": self.session.snapshot(),
            "near_body": self.near_body.snapshot(),
            "far_body": self.far_body.snapshot(),
            "help": self.help.snapshot(),
        }
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

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                self._send(200, INDEX.read_text(), "text/html; charset=utf-8")
                return
            if path == "/proof":
                self._send(200, PROOF.read_text(), "text/html; charset=utf-8")
                return
            if path == "/api/state":
                self._send(200, state.snapshot())
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
                "/api/no_answer": "no_answer",
            }
            try:
                if path == "/api/reset":
                    state.reset()
                    self._send(200, state.snapshot())
                    return
                if path == "/api/emit":
                    body = self._read_json()
                    self._send(200, state.emit(str(body.get("event") or ""), str(body.get("house") or "near")))
                    return
                if path == "/api/scenario":
                    body = self._read_json()
                    self._send(200, state.scenario(str(body.get("name") or "")))
                    return
                if path.startswith("/api/help/"):
                    self._send(200, state.help_act(path.rsplit("/", 1)[-1]))
                    return
                if path == "/api/message":
                    body = self._read_json()
                    self._send(200, state.leave_message(str(body.get("text") or "")))
                    return
                if path == "/api/talk":
                    body = self._read_json()
                    self._send(200, state.talk(str(body.get("text") or ""), str(body.get("speaker") or "near")))
                    return
                if path == "/api/proof":
                    body = self._read_json()
                    self._send(200, state.proof(str(body.get("name") or ""), str(body.get("house") or "near")))
                    return
                if path == "/api/skill":
                    body = self._read_json()
                    self._send(200, state.skill(str(body.get("name") or ""), str(body.get("house") or "near")))
                    return
                if path not in actions:
                    self._send(404, {"error": "not found"})
                    return
                self._send(200, state.act(actions[path]))
            except (ValueError, KeyError) as exc:
                self._send(400, {"error": str(exc), **state.snapshot()})

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5055)
    parser.add_argument("--hal", default="http://127.0.0.1:5001")
    parser.add_argument("--far-hal", default="http://127.0.0.1:5002")
    parser.add_argument("--no-hal", action="store_true")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("call-sam demo binds loopback only")
    near = None if args.no_hal else args.hal
    far = None if args.no_hal else args.far_hal
    state = DemoState(near, far)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    print(f"Use-case demo http://{args.host}:{args.port}/  near={state.hal or 'off'} far={state.far_hal or 'off'}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
