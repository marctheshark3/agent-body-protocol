#!/usr/bin/env bash
# 3. Low power dim — tired is a body state.
# Tired looks like tired, not like an error.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
HAL="${HAL_URL:-http://127.0.0.1:5001}"

echo "==> Low power. Dim."
python3 -m mapper.agent_body power --sim low --hal "$HAL"
