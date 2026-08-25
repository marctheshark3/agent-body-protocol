# Agent Body Protocol

**Coding-agent events in. Autonomous Lamp body language out.**

Agent Body Protocol is a small runtime-neutral contract that makes a physical agent communicate state without becoming another chatty narrator. Claude Code, Hermes, Codex, OpenCode, or CI emit one of nine events. A deterministic mapper returns exact Autonomous OS `[HW:]` sequences and optional short speech.

It consumes Autonomous OS's existing `make sim`. It does not rebuild HAL, fork Buddy, or implement a Grok runtime.

Public gist (idea file): https://gist.github.com/marctheshark3/c7dd087833d3038ad78e593667bca34f

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

```bash
agent-body power --sim mains --record /tmp/power-mains.json
agent-body power --sim battery --record /tmp/power-battery.json
agent-body power --sim qi --record /tmp/power-qi.json
agent-body power --sim low --record /tmp/power-battery-low.json
agent-body power --hal http://127.0.0.1:5001
```

30-second no-hardware script (unplug / walk / pad / thinking stays blue / low dims the head): `scripts/demo_power.sh`. Healthy Qi/USB emit no LED. `--sim low` reaches `power-battery-low.json`. Qi wattage honesty (~5–15 W idle/trickle, not a servo dance) and the ADC → pack-in-base → bench pad path: `docs/POWER.md`.

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

## Demos

- **CI sentinel:** `CI pass` / `CI fail` on the lab page.
- **Pair-programming rubber duck:** thinking stays quiet; permissions turn the body.
- **Help Mode:** `blocked` → consent → point at Send reset link. Never types the secret.
- **Two lamps:** Call Sam. Pat waits, Sam rings.
- **No answer:** leave a 140-char note on Sam’s paired screen.
- **In-call talk:** sanitized transcript on the other screen. Audio stays in the browser.
- **Look / Dance / Stop:** stock HAL verbs on Pat. **Follow** is official `/servo/track` (sim often 500s — no person).

See `docs/DEMO.md` for the 90-second script. Architecture: `docs/ARCHITECTURE.md`. Idea file: `docs/GIST.md`.

```bash
PYTHONPATH=. python3 demos/call-sam/serve.py
# http://127.0.0.1:5055/
PYTHONPATH=. python3 -m mapper.agent_body skill --name dance --hal http://127.0.0.1:5001
PYTHONPATH=. python3 scripts/validate_e2e.py
```

```bash
PYTHONPATH=. python3 -m mapper.agent_body aim --direction user --log /tmp/abp-traj.jsonl
PYTHONPATH=. python3 -m mapper.agent_body transfer --log /tmp/abp-traj.jsonl --hal http://127.0.0.1:5002
```

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
- `docs/POWER.md` — voltage telemetry, battery/Qi path, 30-second `--sim` proof

MIT licensed. Built as a companion extension for Autonomous OS Week 5.
