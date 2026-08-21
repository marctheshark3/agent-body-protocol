"""Loopback-only Agent Body Protocol HTTP server."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .hal_client import dispatch
from .policy import BodyPolicy


class EventHandler(BaseHTTPRequestHandler):
    policy = BodyPolicy()
    hal_url: str | None = None

    def do_POST(self) -> None:
        if self.path != "/event":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            event: dict[str, Any] = json.loads(self.rfile.read(length))
            if event.get("v") != 1 or not isinstance(event.get("event"), str) or not isinstance(event.get("ts"), str):
                raise ValueError("event requires v=1, event, and ts")
            result = self.policy.apply(event)
            dispatched = dispatch(result.output.markers, self.hal_url) if self.hal_url and result.output.markers else []
            self._json(200, {
                "markers": list(result.output.markers),
                "speech": result.output.speech,
                "suppressed": result.suppressed,
                "reason": result.reason,
                "dispatched": dispatched,
            })
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except RuntimeError as exc:
            self._json(502, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = "127.0.0.1", port: int = 5051, hal_url: str | None = None) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("v0 server is loopback-only")
    EventHandler.hal_url = hal_url
    server = ThreadingHTTPServer((host, port), EventHandler)
    print(f"agent-body listening on http://{host}:{port}/event")
    server.serve_forever()
