#!/usr/bin/env python3
"""Post every protocol event's markers to a live HAL and record HTTP evidence."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapper.map import map_event
from mapper.hal_client import parse_marker

EVENTS = (
    "started",
    "thinking",
    "waiting_for_user",
    "permission_required",
    "blocked",
    "tests_passed",
    "tests_failed",
    "completed",
    "quiet",
)


def post(base: str, path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    request = Request(base + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=5) as response:
            raw = response.read()
            parsed = json.loads(raw) if raw else {}
            return {"path": path, "status": response.status, "body": parsed}
    except HTTPError as exc:
        return {"path": path, "status": exc.code, "error": exc.read().decode("utf-8", "replace")}
    except (URLError, TimeoutError) as exc:
        return {"path": path, "status": 0, "error": str(exc)}


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001").rstrip("/")
    with urlopen(base + "/health", timeout=5) as response:
        health = json.loads(response.read())
    evidence = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "hal": base,
        "health": health,
        "events": [],
    }
    failed = 0
    for event in EVENTS:
        mapped = map_event({"v": 1, "event": event, "ts": evidence["ts"], "mode": "focus"})
        results = [post(base, *parse_marker(marker)) for marker in mapped.markers]
        evidence["events"].append({
            "event": event,
            "markers": list(mapped.markers),
            "speech": mapped.speech,
            "results": results,
        })
        if any(item.get("status", 0) >= 400 or item.get("status", 0) == 0 for item in results):
            failed += 1
    out = ROOT / "docs" / "HAL-LIVE.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"wrote": str(out), "failed_events": failed, "health_ok": True}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
