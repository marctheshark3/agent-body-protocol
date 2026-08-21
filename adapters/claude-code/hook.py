#!/usr/bin/env python3
"""Claude Code hook -> Agent Body Protocol adapter."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def classify(hook: str, payload: dict) -> str:
    text = json.dumps(payload).lower()
    if hook in {"SessionStart", "UserPromptSubmit"}:
        return "started"
    if hook == "PermissionRequest":
        return "permission_required"
    if hook == "Notification":
        return "permission_required" if "permission" in text or "needs you" in text else "waiting_for_user"
    if hook in {"PostToolUseFailure", "SubagentStopFailure"}:
        return "blocked"
    if hook == "Stop":
        if any(token in text for token in ("tests passed", "test passed", "0 failed", "passed,")):
            return "tests_passed"
        if any(token in text for token in ("tests failed", "test failed", "failed,")):
            return "tests_failed"
        return "completed"
    return "thinking"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hook", required=True)
    parser.add_argument("--mapper", default="http://127.0.0.1:5051/event")
    parser.add_argument("--mode", choices=("normal", "focus", "night"), default="normal")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    event = {
        "v": 1,
        "event": classify(args.hook, payload),
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "claude-code",
        "mode": args.mode,
    }
    encoded = json.dumps(event, separators=(",", ":")).encode()
    if args.print_only:
        print(encoded.decode())
        return 0
    request = Request(args.mapper, data=encoded, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=2) as response:
        print(response.read().decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
