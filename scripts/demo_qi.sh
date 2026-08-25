#!/usr/bin/env bash
# 4. Qi refuse dance/hatch — pad cannot throw a party.
# A charging pad is not a dance floor. Unplug it if you want it to move.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"

echo "==> On a charger. It will not dance."
python3 -m mapper.agent_body skill --name dance --sim qi
python3 -m mapper.agent_body skill --name hatch --sim qi
