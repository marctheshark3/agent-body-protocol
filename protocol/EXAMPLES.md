# Protocol examples

```json
{"v":1,"event":"thinking","ts":"2026-08-21T18:00:00Z","source":"claude-code","agent":"claude","mode":"focus"}
```

```json
{"v":1,"event":"permission_required","ts":"2026-08-21T18:01:00Z","source":"hermes","summary":"Approve a local test command?","mode":"normal"}
```

```json
{"v":1,"event":"blocked","ts":"2026-08-21T18:02:00Z","source":"codex","summary":"Repeated test failure","consent":"ask"}
```

Unknown fields are rejected. Summaries are limited to 140 characters; details to 2,000. Do not place secrets in either field.
