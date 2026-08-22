#!/usr/bin/env python3
"""Replay an ABP trajectory JSONL onto a HAL (sim or later, real)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapper.transfer import replay


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--hal", required=True)
    parser.add_argument("--out", type=Path, default=Path("/tmp/abp-transfer.jsonl"))
    parser.add_argument("--house", default="sam")
    args = parser.parse_args()
    report = replay(args.log, args.hal, args.out, args.house)
    print(json.dumps({k: report[k] for k in ("ok", "count", "threshold_deg", "failures")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
