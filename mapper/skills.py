"""Named body skills. USB-C to existing HAL verbs. Not RL. Not set_joint."""

from __future__ import annotations

from typing import Any, Mapping

from .hal_client import assert_hal_url, parse_marker, refuse_power_write
from .motion import FORBIDDEN

# Dance is the completed-event choreography (happy_wiggle). Hatch is a second
# named skill — hop then look — not a 10th agent event. completed stays wiggle.
SKILLS = {
    "look": ('[HW:/servo/aim:{"direction":"user"}]',),
    "follow": (
        '[HW:/servo/aim:{"direction":"user"}]',
        '[HW:/servo/track:{"target":["person"]}]',
    ),
    "dance": ('[HW:/servo/play:{"recording":"happy_wiggle"}]',),
    "hatch": (
        # Stock HAL recording: crouch-to-rise on the five joints, interpolated
        # (not an aim teleport). Then a named look. It hops. Then it looks at you.
        '[HW:/servo/play:{"recording":"wake_up"}]',
        '[HW:/servo/aim:{"direction":"user"}]',
    ),
    "stop": (
        '[HW:/servo/track/stop:{}]',
        '[HW:/servo/aim:{"direction":"center"}]',
    ),
}

QI_REFUSE = {
    "dance": "qi-cannot-dance",
    "hatch": "qi-cannot-hatch",
}


class SkillError(ValueError):
    pass


def qi_refuse_reason(name: str, power: Mapping[str, Any] | None) -> str | None:
    """Pad cannot throw a party. dance and hatch refuse on source=qi."""
    key = str(name or "").strip().lower()
    if power and str(power.get("source")) == "qi":
        return QI_REFUSE.get(key)
    return None


def markers_for(name: str, power: Mapping[str, Any] | None = None) -> list[str]:
    key = str(name or "").strip().lower()
    if key not in SKILLS:
        raise SkillError(f"unknown skill: {name!r}")
    markers = list(SKILLS[key])
    # Stock Qi is ~5-15 W and cannot dance or hatch.
    if qi_refuse_reason(key, power):
        return []
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
    base = assert_hal_url(hal_url)
    for marker in markers:
        path, payload = parse_marker(marker)
        refuse_power_write(path)
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
