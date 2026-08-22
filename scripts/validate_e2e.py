#!/usr/bin/env python3
"""Fail-closed end-to-end demo matrix. HTTP 200 is not enough."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapper.call_session import CallSession
from mapper.help_mode import HelpMode
from mapper.map import map_event
from mapper.virtual_body import VirtualBody

EVENTS = [
    "started",
    "thinking",
    "waiting_for_user",
    "permission_required",
    "blocked",
    "tests_passed",
    "tests_failed",
    "completed",
    "quiet",
]


def _get(url: str) -> tuple[int, dict | str]:
    try:
        with urlopen(url, timeout=3) as response:
            raw = response.read()
            try:
                return response.status, json.loads(raw)
            except json.JSONDecodeError:
                return response.status, raw.decode("utf-8", "replace")[:200]
    except URLError as exc:
        return 0, str(exc)


def _post(url: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode()
    req = Request(url, data=data, method="POST")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=4) as response:
            return response.status, json.loads(response.read())
    except URLError as exc:
        return 0, {"error": str(exc)}


def run_units() -> dict:
    stream = StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    return {
        "ok": result.wasSuccessful(),
        "ran": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "tail": stream.getvalue()[-800:],
    }


def run_mapper() -> dict:
    failures = []
    colors = {}
    for name in EVENTS:
        body = VirtualBody("near")
        body.apply(name)
        mapped = map_event(
            {
                "v": 1,
                "event": name,
                "ts": "2026-08-21T00:00:00Z",
                "source": "manual",
            }
        )
        if not mapped.markers and name != "started":
            failures.append(f"{name} produced no markers")
        snap = body.snapshot()
        colors[name] = {"hex": snap["hex"], "effect": snap["effect"], "event": snap["event"]}
    return {"ok": not failures, "failures": failures, "bodies": colors}


def run_use_cases() -> dict:
    cases = {}

    near, far = VirtualBody("near"), VirtualBody("far")
    session = CallSession()
    for house, event in session.dial():
        (near if house == "near" else far).apply(event)
    cases["two_lamp_ring"] = near.event != far.event and far.effect == "pulse"

    session.accept()
    session.talk("hey sam tests are green")
    cases["in_call_talk"] = session.far.heard == "hey sam tests are green" and not session.near.camera_on

    session.hangup()
    session.dial()
    session.no_answer()
    session.leave_message("Call me when you land.")
    cases["no_answer_message"] = session.far.message == "Call me when you land."

    help_mode = HelpMode()
    help_mode.stuck()
    help_mode.consent_yes()
    help_mode.point_reset()
    cases["help_mode"] = help_mode.pointed == "Send reset link"

    ci = VirtualBody("ci")
    for name in ("started", "thinking", "tests_passed", "completed"):
        ci.apply(name)
    cases["ci_pass"] = ci.color[1] > ci.color[0]

    duck = VirtualBody("duck")
    duck.apply("permission_required")
    cases["rubber_duck"] = duck.effect == "pulse"

    return {"ok": all(cases.values()), "cases": cases}


def run_live(hal: str, demo: str) -> dict:
    health_code, health = _get(hal.rstrip("/") + "/health")
    state_code, state = _get(demo.rstrip("/") + "/api/state")
    demo_ok = False
    demo_probe: dict = {}
    if state_code == 200:
        _post(demo.rstrip("/") + "/api/reset")
        code, payload = _post(demo.rstrip("/") + "/api/dial")
        demo_probe = {
            "dial": code,
            "phase": payload.get("session", {}).get("phase"),
            "near": payload.get("near_body", {}).get("event"),
            "far": payload.get("far_body", {}).get("event"),
        }
        miss_code, missed = _post(demo.rstrip("/") + "/api/no_answer")
        msg_code, left = _post(demo.rstrip("/") + "/api/message", {"text": "Call me when you land."})
        demo_probe["no_answer"] = miss_code
        demo_probe["message"] = msg_code
        demo_probe["left"] = (left.get("session") or {}).get("far", {}).get("message")
        _post(demo.rstrip("/") + "/api/reset")
        _post(demo.rstrip("/") + "/api/dial")
        _post(demo.rstrip("/") + "/api/accept")
        talk_code, talked = _post(demo.rstrip("/") + "/api/talk", {"text": "hey sam"})
        demo_probe["talk"] = talk_code
        demo_probe["heard"] = (talked.get("session") or {}).get("far", {}).get("heard")
        help_code, helped = _post(demo.rstrip("/") + "/api/help/stuck")
        demo_probe["help"] = help_code
        demo_probe["help_event"] = ((helped.get("emitted") or [{}])[0]).get("event")
        demo_ok = (
            demo_probe.get("phase") == "ringing"
            and demo_probe.get("near") != demo_probe.get("far")
            and demo_probe.get("left") == "Call me when you land."
            and demo_probe.get("heard") == "hey sam"
            and demo_probe.get("help_event") == "blocked"
        )
    return {
        "ok": health_code == 200 and state_code == 200 and demo_ok,
        "hal_health": health_code,
        "demo_state": state_code,
        "health": health if isinstance(health, dict) else {"raw": health},
        "demo": demo_probe,
    }


def main() -> int:
    hal = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001"
    demo = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5055"
    evidence = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "units": run_units(),
        "mapper": run_mapper(),
        "use_cases": run_use_cases(),
        "live": run_live(hal, demo),
    }
    evidence["ok"] = all(
        evidence[key]["ok"] for key in ("units", "mapper", "use_cases", "live")
    )
    out = ROOT / "docs" / "E2E-VALIDATE.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"wrote": str(out), "ok": evidence["ok"], "units": evidence["units"]["ran"]}))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
