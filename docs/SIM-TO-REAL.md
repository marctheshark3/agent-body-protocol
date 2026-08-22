# Sim-to-real (API, not Isaac)

Train later if we want. Transfer **now** is: log named commands on one HAL, replay the same `[HW:]` on another, measure pose/LED gap.

```bash
# record on Pat (sim)
PYTHONPATH=. python3 -m mapper.agent_body aim --direction user \
  --hal http://127.0.0.1:5001 --log /tmp/abp-pat.jsonl --house pat

# replay on Sam (second sim today; real Lamp later)
PYTHONPATH=. python3 -m mapper.agent_body transfer \
  --log /tmp/abp-pat.jsonl --hal http://127.0.0.1:5002 --house sam \
  --out /tmp/abp-transfer.jsonl
```

## What this is

- Same contract the physical Lamp already speaks (`/servo/aim`, `/led/*`)
- Fail-closed if a log contains `set_joint` / raw pitch
- Gap = max |Δdeg| on the joints HAL actually changes. `left`/`right` score yaw only. `user`/`center`/others **keep current yaw** (upstream mock/animation). Pass < 5°.

## What this is not

- Not MuJoCo / Isaac / domain randomization
- Not a policy. `ABP_AIM_POLICY=learned` is still an empty slot
- Not proof a household Lamp moved
- `/simulator/state` is media-only; joints come from `/servo/position`

Physical transfer is this script with `--hal` pointed at the real HAL. No new protocol.
