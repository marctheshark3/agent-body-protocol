"""Parallel power telemetry contract. Not a tenth agent event."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .map import BodyOutput, _effect, _marker

LOW_VOLTAGE_V = 10.5
LOW_SOC_PCT = 15.0
SOURCES = {"mains", "battery", "qi", "unknown"}
ORIGINS = {"sim", "hal"}
ALLOWED = {"v", "kind", "ts", "voltage_v", "source", "origin", "soc_pct", "charging", "docked", "low"}
SECRET_FIELDS = {"password", "passwd", "token", "secret", "credential", "api_key", "authorization"}

# Per-source expected buses. 5 V on Qi is normal; 5 V on a 3S pack is not.
# These are LED-policy ranges, not BMS cutoffs.
VOLTAGE_RANGE = {
    "mains": (11.0, 14.0),    # 12 V wall rail
    "battery": (9.0, 12.6),   # 3S pack
    "qi": (4.5, 5.5),         # 5 V Qi RX
}

# Approximate 3S Li-ion open-circuit points (pack volts → SOC %).
# This is an OCV lookup for sim/demos. Not a BMS. No current. No temperature.
_SOC_TABLE = (
    (12.60, 100.0),
    (12.45, 90.0),
    (12.30, 80.0),
    (12.15, 70.0),
    (12.00, 60.0),
    (11.85, 50.0),
    (11.55, 40.0),
    (11.40, 30.0),
    (11.10, 20.0),
    (10.80, 15.0),
    (10.50, 10.0),
    (10.20, 5.0),
    (9.00, 0.0),
)

DIM_GREEN = [0, 80, 32]
DIM_LOW = [48, 16, 0]  # slow dim solid; not waiting_for_user amber
WHITE = [200, 200, 200]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def soc_from_voltage(voltage_v: float) -> float:
    """3S OCV table interpolation. Deterministic. Not a BMS."""
    if voltage_v >= _SOC_TABLE[0][0]:
        return _SOC_TABLE[0][1]
    if voltage_v <= _SOC_TABLE[-1][0]:
        return _SOC_TABLE[-1][1]
    for index in range(len(_SOC_TABLE) - 1):
        high_v, high_soc = _SOC_TABLE[index]
        low_v, low_soc = _SOC_TABLE[index + 1]
        if low_v <= voltage_v <= high_v:
            span = high_v - low_v
            t = 0.0 if span == 0 else (voltage_v - low_v) / span
            value = low_soc + t * (high_soc - low_soc)
            return int(value) if value == int(value) else round(value, 1)
    return 0.0


def effective_low(sample: Mapping[str, Any]) -> bool:
    """LED-policy low overlay. Not a pack cutoff. BMS (later) owns cutoff."""
    if sample.get("low") is True:
        return True
    voltage = sample.get("voltage_v")
    soc = sample.get("soc_pct")
    if sample.get("source") == "battery" and isinstance(voltage, (int, float)) and voltage < LOW_VOLTAGE_V:
        return True
    if isinstance(soc, (int, float)) and soc < LOW_SOC_PCT:
        return True
    return False


def validate_power(sample: Any) -> dict[str, Any]:
    if not isinstance(sample, dict):
        raise ValueError("power sample must be a JSON object")
    lowered = {str(key).lower() for key in sample}
    secrets = SECRET_FIELDS & lowered
    if secrets:
        raise ValueError(f"secrets are not allowed in power telemetry: {sorted(secrets)}")
    extra = set(sample) - ALLOWED
    if extra:
        raise ValueError(f"unknown fields: {sorted(extra)}")
    if sample.get("v") != 1:
        raise ValueError("power requires v=1")
    if sample.get("kind") != "power":
        raise ValueError("power requires kind=power")
    ts = sample.get("ts")
    if not isinstance(ts, str) or "T" not in ts:
        raise ValueError("power requires an ISO timestamp")
    if not isinstance(sample.get("voltage_v"), (int, float)) or isinstance(sample.get("voltage_v"), bool):
        raise ValueError("voltage_v must be a number")
    if sample.get("source") not in SOURCES:
        raise ValueError("unknown power source")
    if sample.get("origin") not in ORIGINS:
        raise ValueError("power requires origin=sim|hal")
    if "soc_pct" in sample and sample["soc_pct"] is not None:
        soc = sample["soc_pct"]
        if not isinstance(soc, (int, float)) or isinstance(soc, bool) or not 0 <= soc <= 100:
            raise ValueError("soc_pct must be 0-100 or null")
    for flag in ("charging", "docked", "low"):
        if flag in sample and not isinstance(sample[flag], bool):
            raise ValueError(f"{flag} must be a boolean")
    return sample


def simulate_power(source: str, *, ts: str | None = None) -> dict[str, Any]:
    """Canned demo voltages, always origin=sim. Never label these as HAL."""
    name = str(source or "").strip().lower()
    stamp = ts or utc_now()
    if name == "mains":
        sample = {
            "v": 1,
            "kind": "power",
            "ts": stamp,
            "voltage_v": 12.0,
            "source": "mains",
            "origin": "sim",
            "soc_pct": None,
            "charging": False,
            "docked": True,
            "low": False,
        }
    elif name == "battery":
        voltage = 11.1
        soc = soc_from_voltage(voltage)
        sample = {
            "v": 1,
            "kind": "power",
            "ts": stamp,
            "voltage_v": voltage,
            "source": "battery",
            "origin": "sim",
            "soc_pct": soc,
            "charging": False,
            "docked": False,
            "low": False,
        }
        sample["low"] = effective_low(sample)
    elif name == "qi":
        sample = {
            "v": 1,
            "kind": "power",
            "ts": stamp,
            "voltage_v": 5.0,
            "source": "qi",
            "origin": "sim",
            "soc_pct": None,
            "charging": True,
            "docked": True,
            "low": False,
        }
    else:
        raise ValueError(f"unsupported sim source: {source}")
    return validate_power(sample)


def stamp_hal_origin(sample: Mapping[str, Any]) -> dict[str, Any]:
    """Keep live voltages. Label origin=hal. Do not substitute canned 12.0/11.1/5.0."""
    labeled = dict(sample)
    labeled["origin"] = "hal"
    return validate_power(labeled)


def map_power(sample: Mapping[str, Any]) -> BodyOutput:
    """Map validated power telemetry to existing HAL LED markers only.

    Power is read telemetry. Never emit a /power HAL write.
    Low: slow dim solid. No /servo/aim. Not waiting_for_user amber.
    Qi charging: slow white breathing.
    Charging and docked (USB-C / dock, not the qi-breathing case): dim green solid.
    Mains: stay quiet; wall power is background.
    """
    validated = validate_power(dict(sample))
    if effective_low(validated):
        return BodyOutput((
            _marker("/led/effect/stop", {"transient": True}),
            _marker("/led/solid", {"color": DIM_LOW, "transient": True}),
        ))
    source = str(validated["source"])
    charging = bool(validated.get("charging", False))
    docked = bool(validated.get("docked", False))
    if source == "qi" and charging:
        return BodyOutput((_effect("breathing", WHITE, speed=0.25),))
    if charging and docked:
        return BodyOutput((
            _marker("/led/effect/stop", {"transient": True}),
            _marker("/led/solid", {"color": DIM_GREEN, "transient": True}),
        ))
    return BodyOutput(())
