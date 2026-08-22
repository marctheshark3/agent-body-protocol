---
name: look-follow-dance
description: Named Lamp verbs. look / follow / dance / stop. Never set_joint.
---

# Named body skills

USB-C. The LLM says the verb. HAL already implements it.

```bash
PYTHONPATH=. python3 -m mapper.agent_body skill --name look --hal http://127.0.0.1:5001
PYTHONPATH=. python3 -m mapper.agent_body skill --name dance --hal http://127.0.0.1:5001
PYTHONPATH=. python3 -m mapper.agent_body skill --name follow --hal http://127.0.0.1:5001
PYTHONPATH=. python3 -m mapper.agent_body skill --name stop --hal http://127.0.0.1:5001
```

| Verb | HAL |
|---|---|
| look | `/servo/aim` `user` |
| follow | aim `user` then `/servo/track` `person` |
| dance | `/servo/play` `happy_wiggle` |
| stop | `/servo/track/stop` then aim `center` |

Do not expose joint MCP. Follow needs a camera; the official sim often 500s. That is honest, not a bug in ABP.
