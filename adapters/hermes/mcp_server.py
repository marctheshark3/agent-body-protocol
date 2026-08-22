#!/usr/bin/env python3
"""Minimal stdio MCP tool exposing agent_body_emit."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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

TOOL = {
    "name": "agent_body_emit",
    "description": "Emit a coding-agent lifecycle event to a local Agent Body mapper.",
    "inputSchema": {
        "type": "object",
        "required": ["event"],
        "properties": {
            "event": {"enum": sorted(EVENTS)},
            "summary": {"type": "string", "maxLength": 140},
            "mode": {"enum": ["normal", "focus", "night"]},
            "consent": {"enum": ["off", "ask", "yes"]}
        }
    }
}


def emit(arguments: dict) -> dict:
    name = arguments.get("event")
    if name not in EVENTS:
        raise ValueError("event must be one of the nine protocol events")
    event = {
        "v": 1,
        "event": name,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "hermes",
        "mode": arguments.get("mode", "normal"),
        "consent": arguments.get("consent", "ask"),
    }
    if arguments.get("summary"):
        event["summary"] = arguments["summary"]
    request = Request("http://127.0.0.1:5051/event", data=json.dumps(event).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=2) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise URLError(f"mapper HTTP {exc.code}") from exc


def handle(message: dict) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None
    if method == "initialize":
        result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "agent-body-protocol", "version": "0.1.0"}}
    elif method == "tools/list":
        result = {"tools": [TOOL]}
    elif method == "tools/call" and message.get("params", {}).get("name") == "agent_body_emit":
        try:
            output = emit(message["params"].get("arguments", {}))
        except ValueError as exc:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}
        result = {"content": [{"type": "text", "text": json.dumps(output)}]}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = handle(message if isinstance(message, dict) else {})
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            print(json.dumps(response, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
