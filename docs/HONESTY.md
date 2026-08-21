# Honesty contract

## Proven by this repository

- Nine protocol events validate against the checked-in schema.
- Each event maps deterministically to an exact ordered `[HW:]` sequence.
- LED writes are transient and raw pitch is never emitted.
- Focus/night mode suppresses speech.
- Duplicate events coalesce within two seconds.
- Completion within five seconds of test success skips the second flourish.
- Blocked help offers have a 15-minute cooldown and never emit typing or credential actions.
- The CLI can record all output without a device or network.

## Proven by a live Autonomous OS simulator run

On 2026-08-21, HAL ran with `HAL_SIMULATE=1` on loopback. `/health` reported the Lamp simulator healthy and `/simulator` returned the Autonomous Lamp visualizer. The live validation posted all nine mapped events: 19 route requests, 19 HTTP 200 responses. See `HAL-LIVE.json` for exact paths, payloads, and responses.

This validates the live HAL route/payload contract and simulator execution. The literal `make sim` target was not invoked on this host because its full dependency sync requires system PortAudio headers; the same HAL simulation mode was started directly with Uvicorn.

## Not claimed

- No household Lamp or servo was moved by CI.
- This repo does not ship or replace the Autonomous OS simulator.
- This repo does not implement Autonomous Buddy, Grok, or `AgentGateway`.
- v0 does not provide a public webhook or cloud tunnel.
- v0 test success uses LED only; it avoids the known raw-pitch landmine.
