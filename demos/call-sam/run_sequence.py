#!/usr/bin/env python3
"""Headless Call Sam sequence against optional live HAL."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mapper.call_session import CallSession
from mapper.hal_client import dispatch
from mapper.map import map_event


def run(hal: str | None) -> dict:
    session = CallSession()
    steps = []
    for name in ("start", "invite", "accept", "hangup"):
        emitted = getattr(session, name)()
        bodies = []
        for house, event_name in emitted:
            event = {
                "v": 1,
                "event": event_name,
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "manual",
                "summary": f"{house}:Sam:{name}",
                "mode": "normal",
                "consent": "ask",
            }
            output = map_event(event)
            dispatched = dispatch(list(output.markers), hal) if hal else []
            bodies.append(
                {
                    "house": house,
                    "event": event_name,
                    "markers": list(output.markers),
                    "dispatched": dispatched,
                }
            )
        steps.append({"action": name, "emitted": bodies, "phase": session.phase})
    return {
        "contact": session.contact,
        "hal": hal,
        "final": session.snapshot(),
        "steps": steps,
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    evidence = run(target)
    out = ROOT / "docs" / "CALL-SAM-LIVE.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"wrote": str(out), "phase": evidence["final"]["phase"], "steps": len(evidence["steps"])}))
