---
name: motion-aim
description: Aim the Lamp with named HAL directions only. Use for look-at-user or look-center; not raw joint control, dances, or a new protocol event.
---

# Motion Aim

Look-at is a skill behind `/servo/aim`. It is not a tenth Agent Body event and not an RL MCP.

## Contract

```bash
agent-body aim --direction user --record /tmp/aim.json
```

Allowed directions: `user`, `center`, `left`, `right`, `desk`, `up`, `down`, `wall`.

Default emit:

```text
[HW:/servo/aim:{"direction":"user"}]
```

## Rules

- Coding agents request a **name**, never `wrist_pitch` or `set_joint`.
- One marker. HAL SAFETY still clamps speed.
- `ABP_AIM_POLICY=learned` is a reserved slot. If no module is loaded, fall back to named aim.
- Do not train, download weights, or expose five-DOF tools from this skill.
- Two lamps aim locally. Never write another body's servos.

## Boundaries

Lifecycle color and speech stay on `agent-body`. User-requested mood stays on `emotion` / `led-control`. This skill only aims.
