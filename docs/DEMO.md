# Room demo (90s)

Pat simulator only. Adapter-fired. One lamp. `scripts/demo_power.sh` is the no-hardware table proof, not this script.

Needs Pat `HAL_SIMULATE` on `http://127.0.0.1:5001`. Mapper on loopback. Optional Sam `:5002` only for the last 15s transfer. Fake hook is enough; do not wait on live Claude.

Recording of this script: [`docs/demo/abp-room.mp4`](demo/abp-room.mp4). Receipts: [`docs/demo/abp-room-receipts.json`](demo/abp-room-receipts.json).

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

## 8–55s — stay quiet

```bash
bash scripts/demo_room.sh
```

The script fires the coding loop (thinking / wait / fail / pass / completed), then Help Mode: blocked ask, a real `consent=yes` POST, then point-at-reset. Do not name the events. Do not cycle started or quiet.

After blocked, say: “It asks once. It never types a password.”

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
