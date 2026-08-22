#!/usr/bin/env python3
"""Drive the live ABP lab and capture public-safe stills. Loopback only."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path("/home/marctheshark/Documents/the-grid/agent-body-protocol/docs/demo")
FRAMES = ROOT / "frames"
LAB = "http://127.0.0.1:5055"
PAT = "http://127.0.0.1:5001"


def post(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body or {}).encode()
    req = Request(LAB + path, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=8) as response:
        return json.loads(response.read())


def shot(name: str, url: str) -> Path:
    FRAMES.mkdir(parents=True, exist_ok=True)
    dest = FRAMES / f"{name}.png"
    subprocess.run(
        [
            "firefox",
            "--headless",
            f"--screenshot={dest}",
            "--window-size=1280,720",
            url,
        ],
        check=True,
        timeout=40,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(name, dest.stat().st_size, flush=True)
    return dest


def main() -> int:
    post("/api/reset")
    time.sleep(0.3)
    shot("01-idle", LAB + "/")
    post("/api/scenario", {"name": "ci_pass"})
    time.sleep(0.8)
    shot("02-ci-pass", LAB + "/")
    post("/api/dial")
    time.sleep(0.5)
    shot("03-ring", LAB + "/")
    post("/api/accept")
    time.sleep(0.4)
    shot("04-in-call", LAB + "/")
    dance = post("/api/skill", {"name": "dance", "house": "near"})
    print("dance", json.dumps(dance.get("dispatched"), separators=(",", ":")))
    time.sleep(1.2)
    shot("05-dance", LAB + "/")
    shot("06-pat-sim", PAT + "/simulator")
    look = post("/api/skill", {"name": "look", "house": "near"})
    print("look", json.dumps(look.get("dispatched"), separators=(",", ":")))
    time.sleep(0.8)
    shot("07-look-sim", PAT + "/simulator")
    stop = post("/api/skill", {"name": "stop", "house": "near"})
    print("stop", json.dumps(stop.get("dispatched"), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
