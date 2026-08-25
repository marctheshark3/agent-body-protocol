#!/usr/bin/env bash
# 1. Coding loop — body, not a log.
# You should not have to watch a log. Think, stuck, fail, pass, done — you can see it from across the desk.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
HAL="${HAL_URL:-http://127.0.0.1:5001}"
BEAT="${BEAT:-4}"

post() {
  local event="$1"
  echo "==> $2"
  python3 -m mapper.agent_body post --event "$event" --mode focus --hal "$HAL"
  sleep "$BEAT"
}

post thinking "It thinks."
post waiting_for_user "It looks at you."
post tests_failed "It failed."
post tests_passed "It passed."
post completed "done"
