"""Send mapped HAL markers over HTTP or retain them as evidence."""

from __future__ import annotations

import json
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
POWER_WRITE_PATHS = {"/power", "/sensing/power"}


def assert_hal_url(hal_url: str) -> str:
    parsed = urlparse(hal_url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("HAL URL must be http(s)")
    if host not in LOOPBACK_HOSTS:
        raise ValueError("HAL URL must be loopback")
    return hal_url.rstrip("/")


def parse_marker(marker: str) -> tuple[str, dict]:
    if not marker.startswith("[HW:/") or not marker.endswith("]"):
        raise ValueError(f"invalid HAL marker: {marker!r}")
    path, raw = marker[4:-1].split(":", 1)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("HAL marker payload must be an object")
    return path, payload


def refuse_power_write(path: str) -> None:
    normalized = path.split("?")[0].rstrip("/") or "/"
    if normalized in POWER_WRITE_PATHS or normalized.startswith("/power"):
        raise ValueError(f"refusing HAL write to {path}: power is read telemetry")


def dispatch(markers: Iterable[str], hal_url: str, timeout: float = 3.0) -> list[dict]:
    """POST-only marker dispatch. Never GET. Never POST /power."""
    results = []
    base = assert_hal_url(hal_url)
    for marker in markers:
        path, payload = parse_marker(marker)
        refuse_power_write(path)
        body = json.dumps(payload, separators=(",", ":")).encode()
        request = Request(base + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                results.append({"path": path, "status": response.status})
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"HAL request failed for {path}: {exc}") from exc
    return results


def get_power(hal_url: str, timeout: float = 3.0) -> dict | None:
    """GET power telemetry. Separate from dispatch(); never POST /power.

    Tries `{hal}/power` then `{hal}/sensing/power`. 404, empty body,
    non-object JSON, or JSONDecodeError continue to the next path.
    Both miss → None so the caller labels origin=sim. HAL is a robot
    driver, not currently a sensor. HAL_SIMULATE has no /power.
    """
    base = assert_hal_url(hal_url)
    for path in ("/power", "/sensing/power"):
        request = Request(base + path, method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict) and data:
                    return data
                continue
        except HTTPError as exc:
            try:
                exc.read()
            except Exception:
                pass
            if exc.code == 404:
                continue
            return None
        except (URLError, TimeoutError, ValueError):
            return None
    return None
