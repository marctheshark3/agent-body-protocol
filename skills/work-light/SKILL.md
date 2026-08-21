---
name: work-light
description: Turn on a neutral temporary work light during an explicitly consented Agent Body help session; not general lighting or autonomous screen watching.
---

# Work Light

After the user accepts help, emit:

```text
[HW:/led/effect/stop:{"transient":true}][HW:/led/solid:{"color":[255,255,240],"transient":true}]
```

When help ends, emit:

```text
[HW:/led/restore:{}]
```

Never use this as permission to inspect a screen. The camera and computer-use consent boundaries remain separate.
