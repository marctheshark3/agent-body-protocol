#!/usr/bin/env bash
# No-hardware table proof. NOT the room lead (that is docs/DEMO.md, 90s on HAL).
# Unplug / walk / pad / thinking stays blue / low dims the head / Qi cannot dance.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"

echo "==> 1. Unplug (mains, no LED)"
python3 -m mapper.agent_body power --sim mains --record /tmp/power-mains.json

echo "==> 1b. Phase 1 divider reconstruction (still origin=sim)"
python3 -m mapper.agent_body power --sim adc --record /tmp/power-adc.json

echo "==> 2. Walk (healthy 11.1 V battery is not low)"
python3 -m mapper.agent_body power --sim battery --record /tmp/power-battery.json

echo "==> 3. Pad (healthy Qi, no LED)"
python3 -m mapper.agent_body power --sim qi --record /tmp/power-qi.json

echo "==> 4. Thinking stays blue"
python3 -m mapper.agent_body post --event thinking --record /tmp/thinking.json

echo "==> 5. Low dims the head ([48,16,0])"
python3 -m mapper.agent_body power --sim low --record /tmp/power-battery-low.json

echo "==> dance on Qi refuses happy_wiggle"
python3 -m mapper.agent_body skill --name dance --sim qi
python3 -m mapper.agent_body skill --name hatch --sim qi
