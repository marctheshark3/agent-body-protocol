# Agent Body Protocol

**Coding-agent events in. Autonomous Lamp body language out.**

Coding agents already have a life cycle. The lamp had no word for it. Nine events in. Body language out.

## Room demo (90s)

Pat simulator only. Adapter-fired. One lamp. Script: [`docs/DEMO.md`](docs/DEMO.md). Runner: `scripts/demo_room.sh`.

Hero recording: [`docs/demo/abp-room.mp4`](docs/demo/abp-room.mp4) (Pat `HAL_SIMULATE`, 55s, lamp-only crop). Not `abp-story.mp4`.

```bash
# Autonomous OS — Pat
make sim

# this repo
export PYTHONPATH=.
python3 -m mapper.agent_body serve --host 127.0.0.1 --port 5051 --hal http://127.0.0.1:5001
bash scripts/demo_room.sh
```

Open Pat `http://127.0.0.1:5001/simulator`. No architecture slide. Fake hook is enough; do not wait on live Claude.

Thinking stays blue. Help Mode asks once and never types a password. Same lamp: `--sim low --hal` dims the head, `skill --name dance --sim qi` refuses. USB-C close. Optional look-replay onto Sam is transfer proof only — no ring.

Do not run `scripts/demo.sh` on stage (nine-color parade). Do not play `docs/demo/abp-story.mp4` as the live take (old nine-color + Follow VO). Table proof (no hardware): `scripts/demo_power.sh`. Honesty: [`docs/HONESTY.md`](docs/HONESTY.md).

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
agent-body post --event thinking --record /tmp/thinking.json
python3 -m unittest discover -s tests -v
```

The record contains the exact markers that would be dispatched. Golden files for all nine events live in `fixtures/golden/`.

## Power body

Voltage is a **parallel** contract (`protocol/power.schema.json`), not a 10th agent event. HAL is a robot driver and does not currently expose a battery. Today's Lamp is wall-plugged. This repo ships protocol + simulation; it does not claim HAL already has a pack.

No-hardware table proof: `scripts/demo_power.sh`. Room lead is the 90s on the same lamp (`docs/DEMO.md`): thinking stays blue, `--sim low --hal` dims the head, `skill --name dance --sim qi` refuses the wiggle. Healthy Qi/USB emit no LED. Path and wattage (~5–15 W idle/trickle): `docs/POWER.md`.

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

In Autonomous OS:

```bash
make sim
```

Then in this repo:

```bash
agent-body post --event started --hal http://127.0.0.1:5001
agent-body post --event thinking --hal http://127.0.0.1:5001
agent-body post --event tests_passed --hal http://127.0.0.1:5001
```

Or start the coalescing loopback mapper:

```bash
agent-body serve --hal http://127.0.0.1:5001
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

Room lead is at the top of this README. Table proof: `scripts/demo_power.sh`. Architecture: `docs/ARCHITECTURE.md`. Idea file (not the room script): `docs/GIST.md`. Honesty: `docs/HONESTY.md`.

Old VO `docs/demo/abp-story.mp4` and `docs/demo/story-vo.txt` stay in the tree. They are not the live 90s.

## Repository map

- `protocol/` — JSON Schema and examples
- `mapper/` — deterministic mapper, state policy, loopback server, HAL client, CLI
- `fixtures/golden/` — exact expected marker sequences
- `skills/` — drop-in Agent Body, work-light, build-scribe, motion-aim, look/follow/dance/stop
- `adapters/` — Claude Code and Hermes adapters
- `docs/HONESTY.md` — what the demo does and does not prove
- `docs/ARCHITECTURE.md` — mermaid, nouns, layers
- `docs/architecture.html` — dark architecture diagram
- `docs/SIM-TO-REAL.md` — API replay, not Isaac
- `docs/POWER.md` — voltage telemetry, battery/Qi path, table proof via `scripts/demo_power.sh`
- `docs/GIST.md` — idea file; public gist is the same, not the room script

MIT licensed. Built as a companion extension for Autonomous OS Week 5.
