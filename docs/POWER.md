# Power body

The Lamp is still wall-plugged. HAL is a robot driver, **not a battery gauge**. This PR does not add a 10th agent event (`power_low` is not an event). Voltage is a **parallel** contract: `protocol/power.schema.json`, kind `"power"`.

Phase 0 (this PR) is protocol + simulation + LED mapping onto stock HAL routes. There is no pack in the lamp yet. Do not claim HAL already has a battery. `HAL_SIMULATE` has no `/power`.

Every sample is labeled `origin=sim` or `origin=hal`. Canned 12.0 / 11.1 / 5.0 V voltages are **sim only**. Live GET keeps the HAL numbers.

## 30-second script (no hardware)

Lead demo: unplug / walk / pad / thinking stays blue / low dims the head. Call Sam is not first. No Lamp, no pad, no network. Runnable copy: `scripts/demo_power.sh`.

```bash
python3 -m pip install -e '.[test]'
python3 -m unittest tests.test_power tests.test_help_rails tests.test_schema tests.test_map -q

# 1. Unplug — leave the wall brick. Mains stays quiet (healthy power = no LED).
agent-body power --sim mains --record /tmp/power-mains.json

# 2. Walk — 3S-ish pack sim, healthy 11.1 V, origin=sim. This is NOT low.
agent-body power --sim battery --record /tmp/power-battery.json

# 3. Pad — drop on Qi. Healthy Qi/USB emit no LED (not white breathing, not dim green). origin=sim.
agent-body power --sim qi --record /tmp/power-qi.json

# 4. Thinking stays blue. Power does not steal the agent LED.
agent-body post --event thinking --record /tmp/thinking.json

# 5. Low dims the head. Reaches fixtures/golden/power-battery-low.json.
agent-body power --sim low --record /tmp/power-battery-low.json
# alias: agent-body power --sim battery-low
```

Say this out loud:

1. **Unplug** — markers empty on mains. The body does not nag about wall power.
2. **Walk** — pack lives in the **base**, later. Healthy 11.1 V is not low. `--sim low` is the overlay.
3. **Pad** — healthy Qi/USB emit no LED. Coil-miss is docked + `power_w: 0`.
4. **Thinking stays blue** — `[0,80,255]` breathing. Agent events still win.
5. **Low** — slow dim `[48,16,0]`, **not** `waiting_for_user` amber, **no look-at-user**.

Then the honest line: **stock Qi is ~5–15 W.** Idle/trickle, not a continuous servo dance. `completed` and `skill --name dance` on Qi **refuse `happy_wiggle`**. Work sessions still want the pad or USB-C. `HAL_SIMULATE` has no `/power`; `--hal` 404s and the CLI falls back to **labeled** sim.

Optional live fetch (today 404; origin stays `sim` with `fallback=hal_unavailable`):

```bash
agent-body power --hal http://127.0.0.1:5001 --sim mains
agent-body skill --name dance --sim qi
```

## What shipped (Phase 0)

- `protocol/power.schema.json` — required `{v, kind, ts, voltage_v, source, origin, power_w}`. `power_w` is number or null. Per-source `voltage_v` ranges from `VOLTAGE_RANGE`.
- `mapper/power.py` — validate (consults `VOLTAGE_RANGE`, rejects 5 V mains), simulate (`--sim mains|battery|qi|low`), map to **existing** `/led/*` markers only. Healthy Qi/USB = no LED.
- `get_power()` is a **GET**. `dispatch()` stays POST-only and **refuses** `POST /power`.
- `agent-body power --sim SOURCE` / `--record FILE` / `--hal URL`. `--sim low` or `--sim battery-low` reaches `power-battery-low.json`.
- Golden fixtures: `power-mains.json`, `power-battery-low.json`, `power-qi.json` (JSON, not a 10th `.markers.txt` event golden). All include `power_w`.
- Loopback `GET /power` returns the latest posted sample. Bind stays loopback. HAL URLs are loopback-only.

## Hardware path (not this PR)

| Phase | What | Honest status |
|---|---|---|
| 0 | Protocol + sim + LED mapping | **This PR** |
| 1 | ADC voltage divider on the existing **12 V rail**, still wall-powered | The voltage track. HAL stays a driver; a later GET `/power` can publish the ADC. |
| 2 | 18650/21700 pack + **BMS in the lamp BASE** (not the head). USB-C charge in. | Move between benches with a cable. Do not put cells in the shade. |
| 3 | Qi RX coil in the **base** + a Qi TX pad on each bench | Set the lamp down to charge. |

### Voltage ranges (LED policy, not cutoff)

`validate_power` and the schema consult `VOLTAGE_RANGE` in `mapper/power.py`. 5 V mains is rejected, not treated as low.

| `source` | Bus | Normal | Notes |
|---|---|---|---|
| `mains` | 12 V wall rail | 11.0–14.0 V | 5 V is **invalid**, not mains-low |
| `battery` | 3S pack | 9.0–12.6 V | LED-low if `< 10.5 V` or `soc_pct < 15` (battery-only) |
| `qi` | 5 V Qi RX | 4.5–5.5 V | 5.0 V is **normal**, not low |

`soc_from_voltage` is a **3S OCV lookup table** for sim. It is **not a BMS**. No current. No temperature. `low` is an **LED overlay**, not a pack cutoff. Inferred `soc_pct` low-policy is **battery-only**. A real BMS (Phase 2) owns cutoff, balancing, and thermal.

### Qi wattage (do not oversell)

Stock Qi is about **5–15 W**. Sim uses **5 or 10 W**. Coil-miss: `docked: true`, `charging: false`, `power_w: 0`. Mains `power_w` is required and may be null. Enough to hold idle LEDs and trickle a pack. **Not** enough for continuous servo dance, Follow, or `happy_wiggle` as a primary load. Mapper **refuses the wiggle** when `source=qi` (`completed` and `skill --name dance`). A work session still wants the pad underneath or USB-C.

### Safety (do not ship fiction)

- Use a **BMS**. No homemade pouch packs. No series-cells-with-tape.
- Thermal path in the **base**, away from the LED head.
- Do not describe a UL-unreviewed pack as done. Phase 2/3 are a path, not a product.

## Mapping (deterministic)

| State | Body |
|---|---|
| `low` | Slow dim solid `[48,16,0]`. No `/servo/aim`. Not `waiting_for_user` amber. |
| Healthy Qi / USB-C docked / mains / coil-miss | No extra LED |
| `thinking` + any power | Stays blue. Power does not steal the agent LED. |
| `completed` + `source=qi` | LED flourish only. No `happy_wiggle`. |
| `skill --name dance` + `source=qi` | No `happy_wiggle`. |

Power is **read** telemetry. `get_power` GETs `{hal}/power` then `/sensing/power`. 404 → sim, labeled `origin=sim`. `dispatch()` never POSTs `/power`.
