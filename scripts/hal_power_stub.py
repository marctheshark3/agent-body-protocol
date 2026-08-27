#!/usr/bin/env python3
"""Loopback HAL stand-in for Phase 1 GET /power.

Stock HAL_SIMULATE has no /power. This stub reconstructs voltage_v from a
fake ADS1115 count through the 39.2 kΩ / 10.0 kΩ divider, labeled
origin=hal, source=mains. It is not a battery. It is not live Lamp hardware.
It does not claim HAL already grew GET /power.

    PYTHONPATH=. python3 scripts/hal_power_stub.py --port 5002
    python3 -m mapper.agent_body power --hal http://127.0.0.1:5002

POST /power is refused (405). GET /power and GET /sensing/power return the
same sample. Default count 20114 ≈ 12.37 V so the live number is not canned 12.0.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mapper.hal_client import LOOPBACK_HOSTS
from mapper.power import HAL_STUB_COUNT, ads1115_count_from_vin, sample_from_adc_count, utc_now


class AdcPowerHandler(BaseHTTPRequestHandler):
    count = HAL_STUB_COUNT

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path not in {"/power", "/sensing/power"}:
            self.send_error(404)
            return
        sample = sample_from_adc_count(self.count, ts=utc_now(), origin="hal", source="mains")
        body = json.dumps(sample, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in {"/power", "/sensing/power"} or path.startswith("/power"):
            self.send_error(405, "power is read telemetry")
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 5002, count: int = HAL_STUB_COUNT) -> None:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("HAL power stub is loopback-only")
    AdcPowerHandler.count = count
    server = ThreadingHTTPServer((host, port), AdcPowerHandler)
    print(f"hal-power-stub GET /power on http://{host}:{port} count={count}")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Loopback HAL GET /power stub (Phase 1 ADC, not a pack)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    parser.add_argument("--count", type=int, default=HAL_STUB_COUNT, help="Fake ADS1115 count")
    parser.add_argument("--vin", type=float, help="Override count from a known Vin through the divider")
    args = parser.parse_args(argv)
    count = ads1115_count_from_vin(args.vin) if args.vin is not None else args.count
    serve(args.host, args.port, count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
