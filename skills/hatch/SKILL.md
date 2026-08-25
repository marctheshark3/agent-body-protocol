---
name: hatch
description: Luxo hop then look. After the loop, a hop and a look. Same five joints. Character, not a status light. Not a tenth event. Never set_joint.
---

# Hatch

It hops. Then it looks at you.

Named skill. After the loop, a hop and a look. Same five joints. Character, not a status light. Not a 10th agent event — `completed` still plays `happy_wiggle`.

```bash
PYTHONPATH=. python3 -m mapper.agent_body skill --name hatch
PYTHONPATH=. python3 -m mapper.agent_body skill --name hatch --hal http://127.0.0.1:5001
PYTHONPATH=. python3 -m mapper.agent_body skill --name hatch --sim qi
```

| Power | Body |
|---|---|
| mains / battery | hold off; `/servo/play` `wake_up` (crouch-to-rise, interpolated); wait ~3s; then `/servo/aim` `user` |
| qi | refuse. `markers=[]`. `reason=qi-cannot-hatch`. No hop. |

A charging pad is not a dance floor. Unplug it if you want it to move.

The skill waits out wake_up before aim so HAL does not cancel play.

Do not expose joint MCP. Do not emit `set_joint`. Hatch is not LED-only.
