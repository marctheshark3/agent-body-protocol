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

Power is a **parallel** contract (`kind: "power"`), not a tenth `event` value. Every sample is labeled `origin=sim` or `origin=hal`. See `docs/POWER.md`.

```json
{"v":1,"kind":"power","ts":"2026-08-25T15:00:00Z","voltage_v":12.0,"source":"mains","origin":"sim","soc_pct":null,"charging":false,"docked":true,"low":false,"power_w":null}
```

```json
{"v":1,"kind":"power","ts":"2026-08-25T15:00:00Z","voltage_v":5.0,"source":"qi","origin":"sim","soc_pct":null,"charging":true,"docked":true,"low":false,"power_w":5.0}
```

Qi sim is 5 or 10 W. Coil-miss is on the pad but not coupling (`docked: true`, `charging: false`, `power_w: 0`). Mains `power_w` may be null.

```json
{"v":1,"kind":"power","ts":"2026-08-25T15:00:00Z","voltage_v":5.0,"source":"qi","origin":"sim","soc_pct":null,"charging":false,"docked":true,"low":false,"power_w":0}
```
