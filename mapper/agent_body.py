"""CLI for mapping, posting, and serving Agent Body Protocol events."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .hal_client import dispatch
from .map import map_event
from .motion import ALLOWED_DIRECTIONS, aim
from .policy import BodyPolicy
from .serve import serve
from .trajectory import read_body, record
from .transfer import SETTLE_S, replay


def _event(args: argparse.Namespace) -> dict:
    event = {
        "v": 1,
        "event": args.event,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": args.source,
        "mode": args.mode,
        "consent": args.consent,
    }
    if args.summary:
        event["summary"] = args.summary
    return event


def _result_payload(event: dict, policy: BodyPolicy | None = None) -> dict:
    if policy:
        result = policy.apply(event)
        output = result.output
        suppressed, reason = result.suppressed, result.reason
    else:
        output = map_event(event)
        suppressed, reason = False, None
    return {
        "event": event,
        "markers": list(output.markers),
        "speech": output.speech,
        "suppressed": suppressed,
        "reason": reason,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-body")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("map", "post"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--event", required=True)
        cmd.add_argument("--source", default="manual")
        cmd.add_argument("--mode", choices=("normal", "focus", "night"), default="normal")
        cmd.add_argument("--consent", choices=("off", "ask", "yes"), default="ask")
        cmd.add_argument("--summary")
        cmd.add_argument("--record", type=Path)
        if name == "post":
            cmd.add_argument("--hal", help="HAL base URL; omit for record-only evidence")
            cmd.add_argument("--log", type=Path, help="Append command/state JSONL for later sim-to-real")
    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=5051)
    server.add_argument("--hal")
    aimer = sub.add_parser("aim")
    aimer.add_argument("--direction", required=True, choices=ALLOWED_DIRECTIONS)
    aimer.add_argument("--record", type=Path)
    aimer.add_argument("--hal", help="HAL base URL; omit for record-only evidence")
    aimer.add_argument("--log", type=Path, help="Append command/state JSONL for later sim-to-real")
    aimer.add_argument("--house", default="pat")
    xfer = sub.add_parser("transfer")
    xfer.add_argument("--log", type=Path, required=True)
    xfer.add_argument("--hal", required=True)
    xfer.add_argument("--out", type=Path, default=Path("/tmp/abp-transfer.jsonl"))
    xfer.add_argument("--house", default="sam")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        serve(args.host, args.port, args.hal)
        return 0
    if args.command == "transfer":
        report = replay(args.log, args.hal, args.out, args.house)
        print(json.dumps({k: report[k] for k in ("ok", "count", "threshold_deg", "failures")}, separators=(",", ":")))
        return 0 if report["ok"] else 1
    if args.command == "aim":
        payload = {"direction": args.direction, "markers": aim(args.direction)}
        before = read_body(args.hal) if args.hal else {"ok": False, "error": "no_hal"}
        if args.hal:
            payload["dispatched"] = dispatch(payload["markers"], args.hal)
            time.sleep(SETTLE_S)
        after = read_body(args.hal) if args.hal else before
        if getattr(args, "log", None):
            payload["trajectory"] = record(
                args.log,
                house=getattr(args, "house", "pat"),
                kind="aim",
                command={"direction": args.direction},
                markers=payload["markers"],
                dispatched=payload.get("dispatched"),
                before=before,
                after=after,
            )
        if args.record:
            args.record.write_text(json.dumps(payload, indent=2) + "\n")
        print(json.dumps(payload, separators=(",", ":")))
        return 0
    payload = _result_payload(_event(args))
    before = read_body(args.hal) if args.command == "post" and args.hal else {"ok": False, "error": "no_hal"}
    if args.command == "post" and args.hal:
        payload["dispatched"] = dispatch(payload["markers"], args.hal)
        time.sleep(SETTLE_S)
    if args.command == "post" and getattr(args, "log", None):
        payload["trajectory"] = record(
            args.log,
            house="pat",
            kind="event",
            command={"event": args.event, "source": args.source, "mode": args.mode},
            markers=payload["markers"],
            dispatched=payload.get("dispatched"),
            before=before,
            after=read_body(args.hal) if args.hal else before,
        )
    if args.record:
        args.record.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
