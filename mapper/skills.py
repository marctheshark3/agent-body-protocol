"""Named body skills. USB-C to existing HAL verbs. Not RL. Not set_joint."""

from __future__ import annotations

from typing import Any, Mapping

from .hal_client import parse_marker
from .motion import FORBIDDEN

SKILLS = {
    "look": ('[HW:/servo/aim:{"direction":"user"}]',),
    "follow": (
        '[HW:/servo/aim:{"direction":"user"}]',
        '[HW:/servo/track:{"target":["person"]}]',
    ),
    "dance": ('[HW:/servo/play:{"recording":"happy_wiggle"}]',),
    "stop": (
        '[HW:/servo/track/stop:{}]',
        '[HW:/servo/aim:{"direction":"center"}]',
    ),
}


class SkillError(ValueError):
    pass


def markers_for(name: str, power: Mapping[str, Any] | None = None) -> list[str]:
    key = str(name or "").strip().lower()
    if key not in SKILLS:
        raise SkillError(f"unknown skill: {name!r}")
    # Stock Qi is ~5-15 W and cannot dance. Same overlay as completed.
    if key == "dance" and power and str(power.get("source")) == "qi":
        return []
    markers = list(SKILLS[key])
    blob = "".join(markers).lower()
    for token in FORBIDDEN:
        if token.lower() in blob:
            raise SkillError(f"skill {key} emitted forbidden token: {token}")
    return markers


def dispatch_soft(markers: list[str], hal_url: str, timeout: float = 5.0) -> list[dict[str, Any]]:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
    import json

    results = []
    base = hal_url.rstrip("/")
    for marker in markers:
        path, payload = parse_marker(marker)
        body = json.dumps(payload, separators=(",", ":")).encode()
        request = Request(base + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                results.append(
                    {
                        "path": path,
                        "status": response.status,
                        "body": json.loads(raw) if raw else {},
                    }
                )
        except HTTPError as exc:
            results.append({"path": path, "status": exc.code, "error": exc.read().decode()[:240]})
        except (URLError, TimeoutError) as exc:
            results.append({"path": path, "status": 0, "error": str(exc)})
    return results
