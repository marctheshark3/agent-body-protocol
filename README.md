# Agent Body Protocol

**Coding-agent events in. Autonomous Lamp body language out.**

Agent Body Protocol is a small runtime-neutral contract that makes a physical agent communicate state without becoming another chatty narrator. Claude Code, Hermes, Codex, OpenCode, or CI emit one of nine events. A deterministic mapper returns exact Autonomous OS `[HW:]` sequences and optional short speech.

It consumes Autonomous OS's existing `make sim`. It does not rebuild HAL, fork Buddy, or implement a Grok runtime.

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

## Three demos

- **CI sentinel:** test result becomes green or diagnostic red without narration.
- **Pair-programming rubber duck:** thinking stays alive but quiet; permissions turn the body toward the user.
- **Help Mode:** a blocked agent asks once, then guides a synthetic forgot-password screen without touching the secret field.

## Repository map

- `protocol/` — JSON Schema and examples
- `mapper/` — deterministic mapper, state policy, loopback server, HAL client, CLI
- `fixtures/golden/` — exact expected marker sequences
- `skills/` — drop-in Agent Body, work-light, and build-scribe skills
- `adapters/` — Claude Code and Hermes adapters
- `docs/HONESTY.md` — what the demo does and does not prove

MIT licensed. Built as a companion extension for Autonomous OS Week 5.
