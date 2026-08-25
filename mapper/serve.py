"""Loopback-only Agent Body Protocol HTTP server."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .hal_client import assert_hal_url, dispatch
from .policy import BodyPolicy
from .power import map_power, validate_power

ALLOWED = {"v", "event", "ts", "source", "agent", "summary", "detail", "consent", "mode"}
EVENTS = {
    "started",
    "thinking",
    "waiting_for_user",
    "permission_required",
    "blocked",
    "tests_passed",
    "tests_failed",
    "completed",
    "quiet",
}
SOURCES = {"claude-code", "codex", "hermes", "opencode", "github-actions", "manual"}
MODES = {"normal", "focus", "night"}
CONSENTS = {"off", "ask", "yes"}


def validate_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("event must be a JSON object")
    extra = set(event) - ALLOWED
    if extra:
        raise ValueError(f"unknown fields: {sorted(extra)}")
    if event.get("v") != 1 or event.get("event") not in EVENTS or not isinstance(event.get("ts"), str) or "T" not in event["ts"]:
        raise ValueError("event requires v=1, a known event, and an ISO timestamp")
    if "source" in event and event["source"] not in SOURCES:
        raise ValueError("unknown source")
    if "mode" in event and event["mode"] not in MODES:
        raise ValueError("unknown mode")
    if "consent" in event and event["consent"] not in CONSENTS:
        raise ValueError("unknown consent")
    if "summary" in event and (not isinstance(event["summary"], str) or len(event["summary"]) > 140):
        raise ValueError("summary must be a string of at most 140 characters")
    if "detail" in event and (not isinstance(event["detail"], str) or len(event["detail"]) > 2000):
        raise ValueError("detail must be a string of at most 2000 characters")
    if "agent" in event and (not isinstance(event["agent"], str) or not 1 <= len(event["agent"]) <= 80):
        raise ValueError("agent must be 1-80 characters")
    return event


class EventHandler(BaseHTTPRequestHandler):
    policy = BodyPolicy()
    hal_url: str | None = None
    latest_power: dict[str, Any] | None = None

    def do_GET(self) -> None:
        if self.path != "/power":
            self.send_error(404)
            return
        if self.latest_power is None:
            self.send_error(404)
            return
        self._json(200, self.latest_power)

    def do_POST(self) -> None:
        if self.path == "/power":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                sample = validate_power(json.loads(self.rfile.read(length)))
                EventHandler.latest_power = sample
                output = map_power(sample)
                dispatched = dispatch(output.markers, self.hal_url) if self.hal_url and output.markers else []
                self._json(200, {
                    "sample": sample,
                    "markers": list(output.markers),
                    "speech": output.speech,
                    "dispatched": dispatched,
                })
            except (ValueError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})
            except RuntimeError as exc:
                self._json(502, {"error": str(exc)})
            return
        if self.path != "/event":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            event = validate_event(json.loads(self.rfile.read(length)))
            result = self.policy.apply(event, power=self.latest_power)
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
    EventHandler.hal_url = assert_hal_url(hal_url) if hal_url else None
    server = ThreadingHTTPServer((host, port), EventHandler)
    print(f"agent-body listening on http://{host}:{port}/event")
    server.serve_forever()
