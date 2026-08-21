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

## Proven only when `make sim` is actually running

- HAL accepts the generated route/payload pairs.
- The Autonomous OS simulator visibly renders the LED and motion sequence.

## Not claimed

- No household Lamp or servo was moved by CI.
- This repo does not ship or replace the Autonomous OS simulator.
- This repo does not implement Autonomous Buddy, Grok, or `AgentGateway`.
- v0 does not provide a public webhook or cloud tunnel.
- v0 test success uses LED only; it avoids the known raw-pitch landmine.
