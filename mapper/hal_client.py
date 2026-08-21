"""Send mapped HAL markers over HTTP or retain them as evidence."""

from __future__ import annotations

import json
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parse_marker(marker: str) -> tuple[str, dict]:
    if not marker.startswith("[HW:/") or not marker.endswith("]"):
        raise ValueError(f"invalid HAL marker: {marker!r}")
    path, raw = marker[4:-1].split(":", 1)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("HAL marker payload must be an object")
    return path, payload


def dispatch(markers: Iterable[str], hal_url: str, timeout: float = 3.0) -> list[dict]:
    results = []
    base = hal_url.rstrip("/")
    for marker in markers:
        path, payload = parse_marker(marker)
        body = json.dumps(payload, separators=(",", ":")).encode()
        request = Request(base + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                results.append({"path": path, "status": response.status})
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"HAL request failed for {path}: {exc}") from exc
    return results
