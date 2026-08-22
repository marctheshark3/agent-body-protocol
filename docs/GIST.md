# Agent Body Protocol

**Coding-agent events in. Lamp body language out.**

A coding agent already has a life cycle. It starts. It thinks. It waits. It asks permission. It gets stuck. Tests pass or fail. It finishes. Today that life cycle is text in a terminal. Tomorrow it should be a body.

Agent Body Protocol is a small, runtime-neutral contract: nine named events and four named verbs. A deterministic mapper turns those into Autonomous OS `[HW:]` commands. Claude, Hermes, Codex, or CI can emit them. The Lamp already knows how to move.

Repo: https://github.com/marctheshark3/agent-body-protocol
Gist: https://gist.github.com/marctheshark3/c7dd087833d3038ad78e593667bca34f

**Story (98s):** concept → nine-event language → three scenarios → joint exam → what people add.
https://github.com/marctheshark3/agent-body-protocol/releases/download/lab-demo/abp-story.mp4

Joint receipts (the exam): https://github.com/marctheshark3/agent-body-protocol/releases/download/lab-demo/abp-proof.mp4

Recorded 2026-08-22 against official `HAL_SIMULATE`. `tests_passed` LED `#000000 → #007830`. Look wrist `0 → -85`. Follow `/servo/track` **500** (no person). Dance four joints. HTTP 200 is not a pass — the receipt is the delta.

## The nouns (read these first)

- **HAL** is the Hardware Abstraction Layer — the robot's HTTP driver. It is **not a sensor**.
- **Pat** and **Sam** are two copies of that driver (two pretend houses). Not product names. Not two robot types.
- **`/simulator`** is a 3D preview of HAL. It is **not a physics gym**. Not Isaac.
- **Skill** = a named verb the LLM is allowed to say. USB-C. Not an RL model.

## Nine events

```
started
thinking
waiting_for_user
permission_required
blocked
tests_passed
tests_failed
completed
quiet
```

Quiet by default. Focus/night = light only, no speech. Help Mode on `blocked` asks once and **never types a password**.

## Four verbs (already in HAL)

| You say | HAL already does |
|---|---|
| look | `/servo/aim {direction: user}` |
| dance | `/servo/play {recording: happy_wiggle}` |
| follow | aim user, then `/servo/track {target: ["person"]}` |
| stop | `/servo/track/stop`, aim center |

The LLM does **not** get `set_joint`. If you want "follow me", you plug into `/servo/track`. You do not train a second brain to wiggle five servos.

Follow needs a camera. The official HAL sim often 500s on `/servo/track`. That is honest, not a bug.

## Layers (do not mix)

```
Brain (LLM / CI)
    │  named events + named verbs
    ▼
USB-C (this protocol)
    │  exact [HW:] sequences
    ▼
Body (HAL)
    │  /led  /servo/aim  /servo/play  /servo/track
    ▼
Pat sim · Sam sim · real Lamp later
```

RL, if it ever earns a seat, lives **inside** a named skill (how `user` is reached). It is not an MCP the LLM twiddles.

## Sim-to-real, honestly

Record named commands + LED + joint snapshot on one HAL. Replay the same `[HW:]` on another. Measure the gap.

That is an **exam**, not a training loop. A household Lamp is the same `--hal` URL later. Same protocol. No new stack.

## What this is not

- Not a Grok runtime
- Not a Buddy fork
- Not Isaac
- Not FaceTime on the shade
- Not a trained policy

## Minimum that still wins

Nine events → exact `[HW:]`. Quiet-by-default. Help Mode never types passwords. Look / dance / stop work on the official sim today.

Built as a companion for Autonomous OS Week 5.
