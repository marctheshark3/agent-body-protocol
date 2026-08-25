# Agent Body Protocol

**Coding-agent events in. Lamp body language out.**

This is the idea file. It is **not** the room script.

Live 90s (Pat, fake hook, Help Mode, same-lamp power, USB-C): [`docs/DEMO.md`](DEMO.md) and `scripts/demo_room.sh`.

Repo: https://github.com/marctheshark3/agent-body-protocol
Gist (same idea file): https://gist.github.com/marctheshark3/c7dd087833d3038ad78e593667bca34f

## Old VO (not the room script)

The ~90s story cut is nine colors + Follow + “completed is a wiggle.” Do not play it on stage.
https://github.com/marctheshark3/agent-body-protocol/releases/download/lab-demo/abp-story.mp4

Measured joint and light receipts (table appendix, not the lead):
https://github.com/marctheshark3/agent-body-protocol/releases/download/lab-demo/abp-proof.mp4

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

Quiet by default. At night, light only. If it is stuck, it asks once and **never types a password**.

## Named verbs

| You say | The lamp does |
|---|---|
| look | turns toward you |
| dance | a short celebration |
| hatch | it hops. Then it looks at you. |
| follow | tracks a person, if one is in view |
| stop | stops tracking and centers |

Follow needs a camera and a person. In the simulator there is no person, so follow correctly fails. That is honest, not a bug. Follow is not in the live 90s room script.

## Layers

```
Brain (coding agent or CI)
    │  named events + named verbs
    ▼
This protocol
    │  exact body commands
    ▼
Body (lights and motors)
    │
    ▼
Simulator today · real lamp later
```

## How we prove it

Record the command, the light color, and the joint angles. Play the same command on another body. Measure the gap.

A real lamp later is the same commands. No new stack.

## What people add

- An adapter for the coding agent they already use
- CI that turns the lamp green or red
- New skills only if the body already has the move

Do not teach a second model how to move each joint.

Nine events. Named verbs. The lamp already knows the rest.
