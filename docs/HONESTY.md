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
- Power is a parallel `kind=power` contract, not a 10th agent event. `--sim` proof needs no hardware.
- `dispatch()` is POST-only and refuses `POST /power`. `get_power()` is GET.
- `completed` on `source=qi` refuses `happy_wiggle`.
- `skill --name dance` consults power and also refuses `happy_wiggle` on Qi.
- `skill --name hatch` is hop (`wake_up` recording) then look. Not a 10th event. On Qi: `markers=[]`, `reason=qi-cannot-hatch`. Hatch waits out wake_up before aim so HAL does not cancel play.
- Healthy power (mains, Qi, USB-C docked) emits no LED. Low is dim `[48,16,0]` only.

## Proven by a live Autonomous OS simulator run

On 2026-08-21, HAL ran with `HAL_SIMULATE=1` on loopback. `/health` reported the Lamp simulator healthy and `/simulator` returned the Autonomous Lamp visualizer. The live validation posted all nine mapped events: 19 route requests, 19 HTTP 200 responses. See `HAL-LIVE.json` for exact paths, payloads, and responses.

This validates the live HAL route/payload contract and simulator execution. The literal `make sim` target was not invoked on this host because its full dependency sync requires system PortAudio headers; the same HAL simulation mode was started directly with Uvicorn.

## Not claimed

- No household Lamp or servo was moved by CI.
- This repo does not ship or replace the Autonomous OS simulator.
- This repo does not implement Autonomous Buddy, Grok, or `AgentGateway`.
- v0 does not provide a public webhook or cloud tunnel.
- v0 test success uses LED only; it avoids the known raw-pitch landmine.
- Call Sam is a two-sim ring scenario. It is not a shipping video product, not a real second house, and not a family FaceTime. Public fixtures use the name Sam only.
- In-call “talk” and missed-call notes are sanitized text on a paired-screen stub. Browser mic stays local. Audio/video never ride ABP or MQTT.
- Real-time A/V belongs on a phone/tablet companion (or FaceTime). Do not put faces on the Lamp shade (`display: false`).
- Motion-aim is a named `/servo/aim` slot. `ABP_AIM_POLICY=learned` falls back to named presets until a module exists. No `set_joint` MCP. No training in this repo.
- The trajectory logger (`agent-body aim|post --log`) records command + `/led/color` + `/servo/position` JSONL. `agent-body transfer` replays those markers onto another HAL and reports joint/LED gap. That is **API sim-to-real** (same `[HW:]`, different body). Not Isaac. Not a trained policy. A real Lamp is the same `--hal` later.
- Named skills (`look` / `follow` / `dance` / `hatch` / `stop`) are USB-C onto **stock HAL routes**. Dance is `happy_wiggle`. Hatch is stock `wake_up` (interpolated crouch-to-rise) then named `/servo/aim` `user`. Follow is official `/servo/track`. HAL_SIMULATE has no person — track often 500s. No RL in this repo.
- Hatch hop-then-look is stock `/servo/play` `wake_up` then named `/servo/aim` `user`. `skill --name hatch` waits out wake_up before aim so HAL does not cancel play. Hold is off during play (hold suppresses play). VirtualBody proves the pose sequence in `tests/test_skills.py`. `docs/demo/abp-hatch.mp4` is a HAL_SIMULATE camera recapture of that hop-then-look (mains, not Qi). The mock applies the first `wake_up` frame immediately (snap-into-crouch on frame 1), then interpolates the crouch-to-rise CSV (~3s, many poses), then the named look. Camera orbited onto the user axis so the look is at the viewer (into the shade opening), not the default 3/4 studio. Not LED-only.
- `docs/demo/abp-look.mp4` is the look + Qi hero: named `/servo/aim` `user`, held, then qi-cannot-dance same pose. Named aim, not tracking. Camera orbited onto the user axis so the look is at the viewer (into the shade opening), not the default 3/4 studio. Not the full 90s room (no fail/pass/help). Not hatch.
- `docs/demo/old/abp-room.mp4` is a dashboard take / frozen-pose LED slideshow. Appendix only. Named aim on HAL_SIMULATE interpolates via `/servo/aim`; that is not tracking.
- **HAL_SIMULATE has no `/power`.** A GET 404s; the CLI falls back to labeled `origin=sim`. Do not claim HAL already has a battery.
- **Phase 1** is divider math + GET + a loopback ADC stub (`scripts/hal_power_stub.py`). It is not a soldered ADC in a household Lamp. `--sim adc` stays `origin=sim`. Canned 12.0 / 11.1 / 5.0 V stay `origin=sim`.
- **Phase 2/3 are drawings.** This repo did not ship a pack or Qi hardware. Cells and a UL-listed 3S BMS are TBD.
- **Stock Qi is ~5–15 W** and cannot dance or hatch. Idle/trickle only. Work sessions still want the pad or USB-C. `soc_from_voltage` is a 3S OCV table, not a BMS. `low` is an LED overlay, not a pack cutoff.
