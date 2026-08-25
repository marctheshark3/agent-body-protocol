#!/usr/bin/env bash
# 2. Help Mode asks once — does not type your password.
# It asks once. It does not type your password.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
HAL="${HAL_URL:-http://127.0.0.1:5001}"

echo "==> It asks for help. Once."
python3 -m mapper.agent_body post --event blocked --consent ask --hal "$HAL"
sleep 3
echo "==> consent yes (does not type your password)"
python3 -m mapper.agent_body post --event thinking --consent yes --hal "$HAL"
