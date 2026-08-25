#!/usr/bin/env bash
# 4. Qi refuse dance/hatch — pad cannot throw a party.
# A charging pad is not a dance floor. Unplug it if you want it to move.
# --sim qi --hal so the refuse hits Pat (HAL_SIMULATE has no /power).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
HAL="${HAL_URL:-http://127.0.0.1:5001}"

echo "==> On a charger. It will not dance."
python3 -m mapper.agent_body skill --name dance --sim qi --hal "$HAL"
python3 -m mapper.agent_body skill --name hatch --sim qi --hal "$HAL"
