#!/usr/bin/env bash
# 5. Hatch / Luxo — lamp character, not a test bench.
# It hops. Then it looks at you.
# Skill, not a 10th event. Not LED-only.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
HAL="${HAL_URL:-http://127.0.0.1:5001}"

echo "==> It hops. Then it looks at you."
if [[ "${TABLE:-}" == "1" ]]; then
  python3 -m mapper.agent_body skill --name hatch --sim mains
else
  python3 -m mapper.agent_body skill --name hatch --sim mains --hal "$HAL"
fi
