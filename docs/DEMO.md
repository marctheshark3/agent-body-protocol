# Room demo (90s)

Pat simulator only. Adapter-fired. One lamp. `scripts/demo_power.sh` is the no-hardware table proof, not this script.

Needs Pat `HAL_SIMULATE` on `http://127.0.0.1:5001`. Mapper on loopback. Optional Sam `:5002` only for the last 15s transfer.

```bash
# Autonomous OS — Pat
make sim

# this repo
export PYTHONPATH=.
python3 -m mapper.agent_body serve --host 127.0.0.1 --port 5051 --hal http://127.0.0.1:5001
```

Open Pat `http://127.0.0.1:5001/simulator`. No architecture slide.

## 0–8s

Say: “Coding agents already have a life cycle. The lamp had no word for it. Nine events in. Body language out.”

## 8–40s — the loop

Fire from the Claude/CI adapter (or this fake hook). Do not type `agent-body post --record /tmp` as the lead. Stay quiet while it thinks. Do not name the events. Do not cycle started or quiet.

```bash
export PYTHONPATH=.
MAPPER=http://127.0.0.1:5051/event
HOOK="python3 adapters/claude-code/hook.py --mapper $MAPPER"

echo '{}' | $HOOK --hook PostToolUse
# quiet blue

echo '{}' | $HOOK --hook Notification
# amber, looks at you

echo '{"result":"3 failed"}' | $HOOK --hook Stop
# three red

echo '{"result":"tests passed, 0 failed"}' | $HOOK --hook Stop
# green

echo '{"result":"done"}' | $HOOK --hook Stop
# flourish; dance only off Qi
```

## 40–55s — Help Mode once

blocked → consent → point at reset. Then stop.

```bash
echo '{"error":"tool failed"}' | $HOOK --hook PostToolUseFailure
```

Operator nods. Lamp asks once. Point at Send reset link. Say: “It asks once. It never types a password.”

## 55–75s — same lamp, power

Thinking stays blue. Dim the head on HAL, not in `/tmp`.

```bash
python3 -m mapper.agent_body power --sim low --hal http://127.0.0.1:5001
python3 -m mapper.agent_body skill --name dance --sim qi --hal http://127.0.0.1:5001
```

One sentence: pack in the base later, pad is 5–15 W, not a dance floor. Docked at 0 W is a miss, one clause.

## 75–90s — USB-C

Say: “Same [HW:] they already shipped.”

Optional, Sam on `:5002` only: replay the look as transfer proof. No ring.

```bash
python3 -m mapper.agent_body aim --direction user --log /tmp/abp-look.jsonl --hal http://127.0.0.1:5001
python3 -m mapper.agent_body transfer --log /tmp/abp-look.jsonl --hal http://127.0.0.1:5002
```

## Table proof (no hardware)

Keep `scripts/demo_power.sh`. Unittest suite plus receipts. Not the room lead.

`scripts/demo.sh` parades nine colors and skips blocked. Do not run it on stage.

Honesty: `docs/HONESTY.md`.
