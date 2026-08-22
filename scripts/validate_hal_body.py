#!/usr/bin/env python3
"""Fail-closed live HAL body validation.

Proves joints move independently and LEDs actually change color.
HTTP 200 is not enough.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapper.hal_client import dispatch
from mapper.map import map_event

JOINTS = (
    "base_yaw.pos",
    "base_pitch.pos",
    "elbow_pitch.pos",
    "wrist_pitch.pos",
    "wrist_roll.pos",
)


def _req(url: str, method: str = "GET", body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=4) as response:
        raw = response.read()
        return json.loads(raw) if raw else {"status": response.status}


def get(hal: str, path: str) -> dict:
    return _req(hal.rstrip("/") + path)


def post(hal: str, path: str, body: dict) -> dict:
    return _req(hal.rstrip("/") + path, "POST", body)


def snapshot(hal: str) -> dict:
    color = get(hal, "/led/color")
    pos = get(hal, "/servo/position")
    return {
        "led": color,
        "positions": pos.get("positions") or {},
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def changed_joints(before: dict, after: dict, ignore: set[str] | None = None) -> list[str]:
    ignore = ignore or set()
    out = []
    for name in JOINTS:
        if name in ignore:
            continue
        if abs(float(after.get(name, 0)) - float(before.get(name, 0))) >= 5:
            out.append(name)
    return out


def assert_true(cond: bool, msg: str, failures: list[str]) -> None:
    if not cond:
        failures.append(msg)


def run(hal: str) -> dict:
    failures: list[str] = []
    steps: list[dict] = []

    health = get(hal, "/health")
    assert_true(health.get("led") is True, "HAL led not healthy", failures)
    assert_true(health.get("servo") is True, "HAL servo not healthy", failures)

    post(hal, "/led/off", {})
    time.sleep(0.15)
    dark = snapshot(hal)

    post(hal, "/led/solid", {"color": [0, 200, 80], "transient": False})
    time.sleep(0.15)
    green = snapshot(hal)
    g = green["led"]["color"]
    assert_true(green["led"]["on"] is True, "solid green did not turn LEDs on", failures)
    assert_true(g[1] > g[0] and g[1] > g[2], f"solid green is not green-dominant: {g}", failures)
    assert_true(g[1] > 0, "green channel stayed 0", failures)
    steps.append({"name": "led_solid_green", "before": dark["led"], "after": green["led"]})

    post(hal, "/servo/aim", {"direction": "center", "duration": 0.1})
    time.sleep(0.2)
    center = snapshot(hal)["positions"]
    post(hal, "/servo/aim", {"direction": "left", "duration": 0.1})
    time.sleep(0.2)
    left = snapshot(hal)["positions"]
    yaw_only = changed_joints(center, left)
    assert_true("base_yaw.pos" in yaw_only, f"left aim did not move base_yaw: {yaw_only}", failures)
    assert_true(left["base_yaw.pos"] < -20, f"left yaw not left: {left['base_yaw.pos']}", failures)
    steps.append({"name": "aim_left", "changed": yaw_only, "positions": left})

    post(hal, "/servo/aim", {"direction": "user", "duration": 0.1})
    time.sleep(0.2)
    user = snapshot(hal)["positions"]
    wrist = changed_joints(left, user)
    assert_true("wrist_pitch.pos" in wrist, f"user aim did not move wrist independently: {wrist}", failures)
    assert_true(abs(user["wrist_pitch.pos"] - left["wrist_pitch.pos"]) >= 20, "wrist delta too small", failures)
    steps.append({"name": "aim_user", "changed": wrist, "positions": user})

    events = {}
    for name in (
        "thinking",
        "permission_required",
        "tests_passed",
        "tests_failed",
        "quiet",
    ):
        event = {
            "v": 1,
            "event": name,
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "manual",
            "mode": "normal",
            "consent": "ask",
        }
        output = map_event(event)
        dispatched = dispatch(output.markers, hal)
        time.sleep(0.2)
        now = snapshot(hal)
        events[name] = {
            "markers": list(output.markers),
            "dispatched": dispatched,
            "led": now["led"],
            "positions": now["positions"],
        }
        assert_true(
            all(item.get("status") == 200 for item in dispatched),
            f"{name} had non-200 HAL dispatch",
            failures,
        )

    think = events["thinking"]["led"]
    assert_true(
        think.get("effect") == "breathing" or (think.get("color") or [0, 0, 0])[2] > 0,
        f"thinking did not show blue/breathing: {think}",
        failures,
    )
    passed = events["tests_passed"]["led"]
    pc = passed.get("color") or [0, 0, 0]
    assert_true(pc[1] > pc[0], f"tests_passed not green-dominant: {pc}", failures)

    page = urlopen(hal.rstrip("/") + "/simulator", timeout=4).read().decode()
    assert_true("led = c" in page, "visualizer still does not assign led from /led/color", failures)
    assert_true("drawPreview()" in page, "visualizer still does not draw articulated joints", failures)
    assert_true("uniform mat4 view,proj,model" in page, "visualizer shader still has no model matrix", failures)

    return {
        "ok": not failures,
        "failures": failures,
        "health": health,
        "steps": steps,
        "events": events,
        "hal": hal,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001"
    try:
        report = run(target)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        report = {"ok": False, "failures": [str(exc)], "hal": target}
    out = ROOT / "docs" / "HAL-BODY-VALIDATE.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"wrote": str(out), "ok": report["ok"], "failures": report.get("failures", [])}))
    raise SystemExit(0 if report["ok"] else 1)
