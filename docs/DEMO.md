# 90-second demo

No FaceTime. No Isaac. Two HAL copies + this mapper.

## Nouns

- HAL = robot driver (HTTP), not a sensor
- Pat = `:5001` · Sam = `:5002`
- `/simulator` = 3D preview of that driver

## Start (already running on Spark)

```bash
# Autonomous OS HAL_SIMULATE on :5001 and :5002
PYTHONPATH=. python3 demos/call-sam/serve.py --hal http://127.0.0.1:5001 --far-hal http://127.0.0.1:5002
```

Open:

1. Lab `http://127.0.0.1:5055/`
2. Pat `http://127.0.0.1:5001/simulator`
3. Sam `http://127.0.0.1:5002/simulator`

## Script

1. **CI pass** — Pat goes green.
2. **Call Sam** → **Accept** — paired screens open (not the shade).
3. Type a note → **Send to Sam's screen**.
4. **Dance** — Pat plays `happy_wiggle` (watch the official sim).
5. **Look** — named `/servo/aim user`.
6. **Follow** — official `/servo/track`. Sim often **500** (no person). That is the honest demo.
7. **Stop**.
8. Optional: **Help Mode stuck** → Yes → Point at reset. Never types a password.

## Power body (no hardware, ~30s)

Unplug / walk / pad / thinking stays blue / low dims the head. **Not** a 10th agent event. `HAL_SIMULATE` has no `/power`. Lead script: `scripts/demo_power.sh`.

```bash
agent-body power --sim mains --record /tmp/power-mains.json
agent-body power --sim battery --record /tmp/power-battery.json
agent-body power --sim qi --record /tmp/power-qi.json
agent-body post --event thinking --record /tmp/thinking.json
agent-body power --sim low --record /tmp/power-battery-low.json
```

1. Unplug — mains quiet. 2. Walk — healthy 11.1 V is **not** low. 3. Pad — healthy Qi/USB emit no LED. 4. Thinking stays blue. 5. `--sim low` dims the head `[48,16,0]`, not amber, no look-at-user. **Stock Qi is ~5-15 W** and cannot dance (`completed` and `skill --name dance` refuse `happy_wiggle` on Qi). Full path: `docs/POWER.md`.

## CLI proof

```bash
python3 -m unittest discover -s tests -q
PYTHONPATH=. python3 -m mapper.agent_body skill --name dance --hal http://127.0.0.1:5001
# follow exits 1 on the official sim — camera missing
PYTHONPATH=. python3 -m mapper.agent_body power --sim qi --record /tmp/power-qi.json
PYTHONPATH=. python3 -m mapper.agent_body power --sim low --record /tmp/power-battery-low.json
PYTHONPATH=. python3 -m mapper.agent_body skill --name dance --sim qi
```

## What to say in the thread

Nine events + four verbs. USB-C into HAL they already shipped. Transfer exam is Pat → Sam JSONL, not a gym. Power is a parallel contract so he can move the lamp bench to bench later — protocol now, pack in the base later.

Gist: https://gist.github.com/marctheshark3/c7dd087833d3038ad78e593667bca34f

**Story (~94s):** `docs/demo/abp-story.mp4` — concept, nine colors, three scenarios, joints, add-ons.
**Exam (30s):** `docs/demo/abp-proof.mp4` — live HAL receipts.
