# Agent Body Protocol

Software talks to a body. This lamp thinks, looks at you, and hops when the work is done.

Nine events in. Body language out. Power is a parallel contract, not a 10th event.

## How to run demos

Loopback only. In Autonomous OS (do **not** run `make sim` or `make hal-dev` from this repo — those binds are not loopback):

```bash
HAL_SIMULATE=1 uvicorn hal.server:app --host 127.0.0.1 --port 5001
```

In this repo:

```bash
export PYTHONPATH=.
python3 -m mapper.agent_body serve --host 127.0.0.1 --port 5051 --hal http://127.0.0.1:5001
```

Open `http://127.0.0.1:5001/simulator`. Fake hook is enough; do not wait on live Claude.

Menu: [`docs/DEMO.md`](docs/DEMO.md)

1. **Coding loop** — You should not have to watch a log. Think, stuck, fail, pass, done — you can see it from across the desk. `scripts/demo_coding_loop.sh`
2. **Help Mode** — It asks once. It does not type your password. `scripts/demo_help.sh`
3. **Low power** — Tired looks like tired, not like an error. `scripts/demo_low.sh`
4. **Qi** — A charging pad is not a dance floor. Unplug it if you want it to move. `scripts/demo_qi.sh`
5. **Hatch** — When the work is done, it hops and looks at you. Same five joints. Character, not a status light. `scripts/demo_hatch.sh`
6. **USB-C** — Unplug it and take it with you. `scripts/demo_usbc.sh`

Hatch CLI: `python3 -m mapper.agent_body skill --name hatch`

It hops. Then it looks at you.

Combined 90s room take (coding loop + help): `scripts/demo_room.sh`. Table proof (no hardware): `scripts/demo_power.sh`.

Captions (lamp-only recapture, when reshot):

- It thinks.
- It looks at you.
- It failed.
- It passed.
- It asks for help. Once.
- Low power. Dim.
- On a charger. It will not dance.
- It hops. Then it looks at you.

Slot: [`docs/demo/abp-room.mp4`](docs/demo/abp-room.mp4). Current file is a dashboard take / frozen-pose LED slideshow, **not** a locked lamp recapture. Do not present it as tracking, Luxo hatch, or a joints-locked hero. A named-aim recapture (HAL_SIMULATE snaps; not tracking) is not this branch's hero. Hatch is a live skill, not in that file. Not `abp-story.mp4`.

Do not run `scripts/demo.sh` on stage (nine-color parade). Honesty: [`docs/HONESTY.md`](docs/HONESTY.md).

## The contract

- `started` — dim white, silent
- `thinking` — slow blue breathing, silent
- `waiting_for_user` — amber pulse, looks toward user
- `permission_required` — amber attention, asks once
- `blocked` — red diagnostic breathing, offers help once with consent
- `tests_passed` — green, optional two-word report
- `tests_failed` — three red flashes, optional two-word report
- `completed` — short green flourish, silent
- `quiet` — stop speech, restore the user's LED state

Every LED write is transient. Focus/night modes are silent. No mapping drives raw servo pitch.

## Quick proof — no hardware or network

```bash
python3 -m pip install -e '.[test]'
python3 -m mapper.agent_body post --event thinking --record /tmp/thinking.json
python3 -m pytest tests -q
```

The record contains the exact markers that would be dispatched. Golden files for all nine events live in `fixtures/golden/`.

## Power body

Voltage is a **parallel** contract (`protocol/power.schema.json`), not a 10th agent event. HAL is a robot driver and does not currently expose a battery. Today's Lamp is wall-plugged. This repo ships protocol + simulation; it does not claim HAL already has a pack.

No-hardware table proof: `scripts/demo_power.sh`. Same lamp: `--sim low --hal` dims the head, `skill --name dance --sim qi` and `skill --name hatch --sim qi` refuse. Healthy Qi/USB emit no LED. Path and wattage (~5–15 W idle/trickle): `docs/POWER.md`.

## Live HAL validation

Validated on 2026-08-21 against the Autonomous OS Lamp simulator running live with `HAL_SIMULATE=1` on `127.0.0.1:5001`:

- HAL health: `status=ok`; servo, LED, camera, audio, sensing, voice, TTS, and music reported healthy.
- Simulator page returned `Autonomous Lamp`.
- All nine events dispatched **19 HAL requests; 19 returned HTTP 200**.
- Exact request/response evidence is checked in at `docs/HAL-LIVE.json`.

Re-run the proof with:

```bash
python3 scripts/validate_hal.py http://127.0.0.1:5001
```

## Run against Autonomous OS

Start HAL on loopback (not `make sim`):

```bash
HAL_SIMULATE=1 uvicorn hal.server:app --host 127.0.0.1 --port 5001
```

Then in this repo:

```bash
python3 -m mapper.agent_body post --event started --hal http://127.0.0.1:5001
python3 -m mapper.agent_body post --event thinking --hal http://127.0.0.1:5001
python3 -m mapper.agent_body post --event tests_passed --hal http://127.0.0.1:5001
python3 -m mapper.agent_body skill --name hatch --hal http://127.0.0.1:5001
```

Or start the coalescing loopback mapper:

```bash
python3 -m mapper.agent_body serve --host 127.0.0.1 --port 5051 --hal http://127.0.0.1:5001
curl -s http://127.0.0.1:5051/event \
  -H 'Content-Type: application/json' \
  -d '{"v":1,"event":"blocked","ts":"2026-08-21T18:00:00Z","source":"manual","consent":"ask"}'
```

The v0 server binds to loopback only. Speech is returned to the caller as one optional line; no undocumented HAL speech endpoint is invented.

## Adapters

- `adapters/claude-code/hook.py` maps explicit Claude Code hook payloads.
- `adapters/hermes/mcp_server.py` exposes `agent_body_emit` over stdio MCP.
- Codex/OpenCode use the runtime-neutral `agent-body post` CLI in v0.
- GitHub Actions is documented for self-hosted/LAN runners only. No public tunnel.

## Consent-gated Help Mode

`blocked` is the entry point, not a separate surveillance product.

1. Offer help once; 15-minute cooldown.
2. Continue only after consent.
3. Explain or click non-secret controls.
4. Never read, store, OCR, or type passwords, credentials, tokens, or recovery codes.
5. Never run always-on screen watch.

`tests/test_help_rails.py` fails if any blocked mapping emits credential or typing actions.

## Demos (appendix)

Room menu is at the top of this README. Table proof: `scripts/demo_power.sh`. Architecture: `docs/ARCHITECTURE.md`. Idea file (not the room script): `docs/GIST.md`. Honesty: `docs/HONESTY.md`.

Old VO `docs/demo/abp-story.mp4` and `docs/demo/story-vo.txt` stay in the tree. They are not the live take.

## Repository map

- `protocol/` — JSON Schema and examples
- `mapper/` — deterministic mapper, state policy, loopback server, HAL client, CLI
- `fixtures/golden/` — exact expected marker sequences
- `skills/` — drop-in Agent Body, work-light, build-scribe, motion-aim, look/follow/dance/hatch/stop
- `adapters/` — Claude Code and Hermes adapters
- `docs/HONESTY.md` — what the demo does and does not prove
- `docs/ARCHITECTURE.md` — mermaid, nouns, layers
- `docs/architecture.html` — dark architecture diagram
- `docs/SIM-TO-REAL.md` — API replay, not Isaac
- `docs/POWER.md` — voltage telemetry, battery/Qi path, table proof via `scripts/demo_power.sh`
- `docs/GIST.md` — idea file; public gist is the same, not the room script

MIT licensed. Built as a companion extension for Autonomous OS Week 5.
