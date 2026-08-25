# Stage demo (30s, no hardware)

This is the win script. Do not start with Call Sam. Do not dance on mains and call it Qi.

Lamp leaves the wall later. Today: protocol + sim, labeled `origin=sim`. Not a 10th agent event. HAL has no `/power`.

```bash
python3 -m pip install -e '.[test]'
python3 -m unittest tests.test_power tests.test_help_rails tests.test_schema tests.test_map -q
bash scripts/demo_power.sh
```

Or by hand:

```bash
export PYTHONPATH=.
python3 -m mapper.agent_body power --sim mains --record /tmp/power-mains.json
python3 -m mapper.agent_body power --sim battery --record /tmp/power-battery.json
python3 -m mapper.agent_body power --sim qi --record /tmp/power-qi.json
python3 -m mapper.agent_body post --event thinking --record /tmp/thinking.json
python3 -m mapper.agent_body power --sim low --record /tmp/power-battery-low.json
python3 -m mapper.agent_body skill --name dance --sim qi
```

Say this out loud while it runs:

1. **Unplug** — mains. `markers: []`. Wall power does not nag.
2. **Walk** — `--sim battery` is healthy 11.1 V, **not** low. Pack lives in the base later.
3. **Pad** — `--sim qi`. Healthy Qi emits no LED (not white, not dim green). `origin=sim`. Stock Qi is ~5–15 W.
4. **Thinking stays blue** — `[0,80,255]` breathing. Power does not steal the agent LED.
5. **Low dims the head** — `--sim low` is `/led/solid [48,16,0]`. Not waiting amber. No look-at-user.
6. **Qi cannot dance** — `skill --name dance --sim qi` returns `markers: []` and `qi-cannot-dance`. Do not run `skill --name dance` without `--sim qi` on stage.

Every `--sim` record is `origin=sim`. `dispatch()` never POSTs `/power`.

## Optional: Call Sam (not first, needs HAL)

Only after the 30s. Needs `HAL_SIMULATE` on `:5001` and `:5002`, which this box often does not have. Follow 500s without a person is the honest sim.

```bash
PYTHONPATH=. python3 demos/call-sam/serve.py --hal http://127.0.0.1:5001 --far-hal http://127.0.0.1:5002
```

Lab `http://127.0.0.1:5055/` · Pat `:5001/simulator` · Sam `:5002/simulator`.

If you dance here, you are on mains. On Qi it refuses.
