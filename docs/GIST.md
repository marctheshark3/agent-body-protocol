# Agent Body Protocol

**Coding-agent events in. Lamp body language out.**

A coding agent already has a life cycle. It starts. It thinks. It waits. It asks permission. It gets stuck. Tests pass or fail. It finishes. Today that life lives in a terminal. A lamp has no word for it.

Agent Body Protocol is a small contract: nine named events and four named verbs. A coding agent speaks them. The lamp already knows how to move.

Repo: https://github.com/marctheshark3/agent-body-protocol
Gist: https://gist.github.com/marctheshark3/c7dd087833d3038ad78e593667bca34f

**Story (about 90s):** why this exists, the nine colors, three everyday asks, then how we prove the joints moved.
https://github.com/marctheshark3/agent-body-protocol/releases/download/lab-demo/abp-story.mp4

Measured joint and light receipts: https://github.com/marctheshark3/agent-body-protocol/releases/download/lab-demo/abp-proof.mp4

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

## Four verbs

| You say | The lamp does |
|---|---|
| look | turns toward you |
| dance | a short celebration |
| follow | tracks a person, if one is in view |
| stop | stops tracking and centers |

Follow needs a camera and a person. In the simulator there is no person, so follow correctly fails. That is honest, not a bug.

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

Nine events. Four verbs. The lamp already knows the rest.
