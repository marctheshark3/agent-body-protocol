#!/usr/bin/env bash
# 30-second no-hardware power demo.
# Unplug / walk / pad / coil-miss / thinking stays blue / low dims the head.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"

echo "==> 1. Unplug (mains, no LED)"
python3 -m mapper.agent_body power --sim mains --record /tmp/power-mains.json

echo "==> 2. Walk (healthy 11.1 V battery is not low)"
python3 -m mapper.agent_body power --sim battery --record /tmp/power-battery.json

echo "==> 3. Pad (healthy Qi, no LED)"
python3 -m mapper.agent_body power --sim qi --record /tmp/power-qi.json

echo "==> 4. Coil-miss (docked, 0 W, no LED)"
python3 -m mapper.agent_body power --sim coil-miss --record /tmp/power-coil-miss.json

echo "==> 5. Thinking stays blue"
python3 -m mapper.agent_body post --event thinking --record /tmp/thinking.json

echo "==> 6. Low dims the head ([48,16,0])"
python3 -m mapper.agent_body power --sim low --record /tmp/power-battery-low.json

echo "==> dance on Qi refuses happy_wiggle"
python3 -m mapper.agent_body skill --name dance --sim qi
