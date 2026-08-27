"""Parallel power telemetry contract. Not a tenth agent event."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .map import BodyOutput, _marker

LOW_VOLTAGE_V = 10.5
LOW_SOC_PCT = 15.0
SOURCES = {"mains", "battery", "qi", "unknown"}
ORIGINS = {"sim", "hal"}
ALLOWED = {"v", "kind", "ts", "voltage_v", "source", "origin", "soc_pct", "charging", "docked", "low", "power_w"}
SECRET_FIELDS = {"password", "passwd", "token", "secret", "credential", "api_key", "authorization"}

# Per-source expected buses. 5 V on Qi is normal; 5 V on a 3S pack is not.
# These are LED-policy ranges, not BMS cutoffs. validate_power consults this table.
VOLTAGE_RANGE = {
    "mains": (11.0, 14.0),    # 12 V wall rail
    "battery": (9.0, 12.6),   # 3S pack
    "qi": (4.5, 5.5),         # 5 V Qi RX
}

# Phase 1 voltage divider on the existing 12 V wall rail, in the BASE (not the head).
# First principles: Vadc = Vin * R_low / (R_high + R_low).
# 30 kΩ / 10 kΩ is the class (tens of kΩ, ~3:1). At 14 V that is 3.50 V, which
# exceeds a 3.3 V ADC. Tighten to E96 1% 39.2 kΩ / 10.0 kΩ:
#   ratio = 10 / 49.2 ≈ 0.203252
#   12.0 V → 2.439 V
#   14.0 V → 2.846 V  (0.454 V margin below 3.3 V)
# ESP ADC is not trusted (nonlinear). Named ADC: Adafruit ADS1115 1085.
# PGA FS ±4.096 V; analog pin must still stay under VDD (3.3 V on the Lamp MCU).
R_HIGH_OHM = 39200.0
R_LOW_OHM = 10000.0
ADC_VREF_V = 3.3
ADS1115_FSR_V = 4.096
ADS1115_POS_MAX = 32768  # 2**15
ADS1115_LSB_V = ADS1115_FSR_V / ADS1115_POS_MAX  # 125 µV
# Nominal 12.0 V rail through one ADS1115 LSB. Reconstructed voltage is 11.99988, not canned 12.0.
ADC_SIM_COUNT = 19512
# HAL stub default: a live-looking 12.37 V so origin=hal is not a canned 12.0.
HAL_STUB_COUNT = 20114


def divider_ratio() -> float:
    return R_LOW_OHM / (R_HIGH_OHM + R_LOW_OHM)


def vadc_from_vin(vin_v: float) -> float:
    return float(vin_v) * divider_ratio()


def vin_from_vadc(vadc_v: float) -> float:
    return float(vadc_v) * (R_HIGH_OHM + R_LOW_OHM) / R_LOW_OHM


def ads1115_count_from_vadc(vadc_v: float) -> int:
    return int(round(float(vadc_v) / ADS1115_LSB_V))


def vadc_from_ads1115_count(count: int) -> float:
    return int(count) * ADS1115_LSB_V


def ads1115_count_from_vin(vin_v: float) -> int:
    return ads1115_count_from_vadc(vadc_from_vin(vin_v))


def vin_from_ads1115_count(count: int) -> float:
    return vin_from_vadc(vadc_from_ads1115_count(count))


def divider_trace(count: int) -> dict[str, Any]:
    vadc = vadc_from_ads1115_count(count)
    return {
        "count": int(count),
        "vadc_v": vadc,
        "voltage_v": vin_from_vadc(vadc),
        "r_high_ohm": R_HIGH_OHM,
        "r_low_ohm": R_LOW_OHM,
        "fsr_v": ADS1115_FSR_V,
    }


def sample_from_adc_count(
    count: int,
    *,
    ts: str | None = None,
    origin: str = "hal",
    source: str = "mains",
) -> dict[str, Any]:
    """Reconstruct a power sample from an ADS1115 count through the Phase 1 divider.

    origin=hal is for a HAL that actually returned a count/voltage.
    --sim adc still labels origin=sim. Never substitute canned 12.0.
    """
    voltage = vin_from_ads1115_count(count)
    stamp = ts or utc_now()
    sample = {
        "v": 1,
        "kind": "power",
        "ts": stamp,
        "voltage_v": voltage,
        "source": source,
        "origin": origin,
        "soc_pct": None,
        "charging": False,
        "docked": True,
        "low": False,
        "power_w": None,
    }
    return validate_power(sample)


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

DIM_LOW = [48, 16, 0]  # slow dim solid; not waiting_for_user amber


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
    """LED-policy low overlay. Not a pack cutoff. BMS (later) owns cutoff.

    Inferred voltage/soc low is battery-only. An explicit low=true still wins.
    """
    if sample.get("low") is True:
        return True
    if sample.get("source") != "battery":
        return False
    voltage = sample.get("voltage_v")
    soc = sample.get("soc_pct")
    if isinstance(voltage, (int, float)) and not isinstance(voltage, bool) and voltage < LOW_VOLTAGE_V:
        return True
    if isinstance(soc, (int, float)) and not isinstance(soc, bool) and soc < LOW_SOC_PCT:
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
    voltage = sample.get("voltage_v")
    if not isinstance(voltage, (int, float)) or isinstance(voltage, bool):
        raise ValueError("voltage_v must be a number")
    if sample.get("source") not in SOURCES:
        raise ValueError("unknown power source")
    if sample.get("origin") not in ORIGINS:
        raise ValueError("power requires origin=sim|hal")
    source = sample.get("source")
    if source in VOLTAGE_RANGE:
        lo, hi = VOLTAGE_RANGE[source]
        if not lo <= float(voltage) <= hi:
            raise ValueError(f"voltage_v {voltage} out of range for {source} ({lo}-{hi} V)")
    if "soc_pct" in sample and sample["soc_pct"] is not None:
        soc = sample["soc_pct"]
        if not isinstance(soc, (int, float)) or isinstance(soc, bool) or not 0 <= soc <= 100:
            raise ValueError("soc_pct must be 0-100 or null")
    if "power_w" not in sample:
        raise ValueError("power_w is required (number or null)")
    if sample["power_w"] is not None:
        power_w = sample["power_w"]
        if not isinstance(power_w, (int, float)) or isinstance(power_w, bool) or power_w < 0:
            raise ValueError("power_w must be >= 0 or null")
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
            "power_w": None,
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
            "power_w": None,
        }
        sample["low"] = effective_low(sample)
    elif name in ("low", "battery-low"):
        # Golden fixtures/golden/power-battery-low.json. Healthy 11.1 V is --sim battery.
        sample = {
            "v": 1,
            "kind": "power",
            "ts": stamp,
            "voltage_v": 10.2,
            "source": "battery",
            "origin": "sim",
            "soc_pct": 8,
            "charging": False,
            "docked": False,
            "low": True,
            "power_w": None,
        }
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
            "power_w": 5.0,
        }
    elif name == "adc":
        # Phase 1 divider reconstruction. Still origin=sim — this is not HAL.
        # HAL_SIMULATE has no GET /power. Use scripts/hal_power_stub.py for origin=hal.
        return sample_from_adc_count(ADC_SIM_COUNT, ts=stamp, origin="sim", source="mains")
    else:
        raise ValueError(f"unsupported sim source: {source}")
    return validate_power(sample)


def stamp_hal_origin(sample: Mapping[str, Any]) -> dict[str, Any]:
    """Keep live voltages. Label origin=hal. Do not substitute canned 12.0/11.1/5.0."""
    labeled = dict(sample)
    labeled["origin"] = "hal"
    if "power_w" not in labeled:
        labeled["power_w"] = None
    return validate_power(labeled)


def map_power(sample: Mapping[str, Any]) -> BodyOutput:
    """Map validated power telemetry to existing HAL LED markers only.

    Power is read telemetry. Never emit a /power HAL write.
    Low: slow dim solid [48,16,0]. No /servo/aim. Not waiting_for_user amber.
    Healthy power (mains, Qi charging, USB-C docked, coil-miss 0 W): no LED.
    Agent events still win: thinking stays blue.
    """
    validated = validate_power(dict(sample))
    if effective_low(validated):
        return BodyOutput((
            _marker("/led/effect/stop", {"transient": True}),
            _marker("/led/solid", {"color": DIM_LOW, "transient": True}),
        ))
    return BodyOutput(())
