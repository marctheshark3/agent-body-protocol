---
name: agent-body
description: Express coding-agent lifecycle events through Lamp body language. Use for started, thinking, waiting, permission, blocked, test, completion, and quiet states; not user-requested colors or general conversation emotion.
---

# Agent Body

Translate coding-agent lifecycle into restrained Lamp behavior through Agent Body Protocol v1.

## Contract

Emit one event to the local mapper:

```bash
agent-body post --event <event> --source <source> --hal http://127.0.0.1:5001
```

Events: `started`, `thinking`, `waiting_for_user`, `permission_required`, `blocked`, `tests_passed`, `tests_failed`, `completed`, `quiet`.

Use `--mode focus` or `--mode night` to suppress speech. Use `--consent off` to disable the help offer.

## Behavior rules

- Quiet by default: never narrate `started` or `thinking`.
- Ask permission once. Do not mention prompt IDs, HTTP, MCP, or Buddy.
- `blocked` may offer help once only when consent is not off.
- Help mode never reads, stores, OCRs, or types passwords or credentials.
- Camera use requires the user's explicit request or an already-consented help session.
- Computer control requires a paired companion and is limited to non-secret controls.
- Every LED write is transient; preserve the user's chosen color.
- Do not emit raw servo pitch. v0 test success is LED-only.

## Boundaries

Use `led-control` for a user-requested color, `scene` for ambience, `emotion` for conversation, and `claude-buddy` for voice approval transport. This skill owns only agent lifecycle body language.
