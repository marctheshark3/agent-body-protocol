# Demo menu

Software talks to a body. This lamp thinks, looks at you, and will not dance on a charger.

Loopback only. Fake hook is enough; do not wait on live Claude.

```bash
# Autonomous OS — Pat (loopback; do not use make sim / make hal-dev)
HAL_SIMULATE=1 uvicorn hal.server:app --host 127.0.0.1 --port 5001

# this repo
export PYTHONPATH=.
python3 -m mapper.agent_body serve --host 127.0.0.1 --port 5051 --hal http://127.0.0.1:5001
```

Open `http://127.0.0.1:5001/simulator`.

Hatch CLI: `python3 -m mapper.agent_body skill --name hatch`

It hops. Then it looks at you.

Captions (lamp-only recapture, when reshot):

- It thinks.
- It looks at you.
- It failed.
- It passed.
- It asks for help. Once.
- Low power. Dim.
- On a charger. It will not dance.
- It hops. Then it looks at you.

Look + Qi hero: [`docs/demo/abp-look.mp4`](demo/abp-look.mp4). Named `/servo/aim` `user`, held, then qi-cannot-dance same pose. Named aim, not tracking. Not the full 90s room (no fail/pass/help). Not hatch.

[`docs/demo/abp-room.mp4`](demo/abp-room.mp4) on main is still the dashboard take / frozen-pose LED slideshow. Do not claim it is this lock. Hatch joints-moved is VirtualBody/tests until a HAL_SIMULATE `wake_up` recapture exists. Do not claim camera hatch. Hatch is a live skill, not in that file. Not `abp-story.mp4`.

## 1. Coding loop

You should not have to watch a log. Think, stuck, fail, pass, done — you can see it from across the desk.

```bash
bash scripts/demo_coding_loop.sh
```

## 2. Help Mode

It asks once. It does not type your password.

```bash
bash scripts/demo_help.sh
```

## 3. Low power

Tired looks like tired, not like an error.

```bash
bash scripts/demo_low.sh
```

Low power. Dim.

## 4. Qi

A charging pad is not a dance floor. Unplug it if you want it to move.

```bash
bash scripts/demo_qi.sh
```

On a charger. It will not dance.

## 5. Hatch

After the loop, a hop and a look. Same five joints. Character, not a status light.

```bash
bash scripts/demo_hatch.sh
```

When the work is done, it hops and looks at you.

It hops. Then it looks at you.

Hatch is a **skill**, not a 10th event. `completed` still plays `happy_wiggle`. Hatch is script #5, not the done beat. On Qi: no hop, `markers=[]`, `reason=qi-cannot-hatch`. Joints-moved is VirtualBody/tests until a HAL_SIMULATE `wake_up` recapture exists. Do not claim camera hatch.

## 6. USB-C

Unplug it and take it with you.

```bash
bash scripts/demo_usbc.sh
```

Spoken/pantomime: unplug the cable and walk. This script does not unplug. A `/tmp --record` is not unplug-and-go. No Call Sam. No Follow.

## Combined 90s room take

Coding loop + help, adapter-fired: `scripts/demo_room.sh`. Presenter stays quiet during the script. After blocked, say: “It asks once. It never types a password.” Then run the focused power / Qi / hatch scripts rather than one parade.

## Table proof (no hardware)

Keep `scripts/demo_power.sh`. Unittest suite plus receipts. Not the room lead.

`scripts/demo.sh` parades nine colors and skips blocked. Do not run it on stage.

Honesty: `docs/HONESTY.md`. Idea file (not this menu): `docs/GIST.md`.
