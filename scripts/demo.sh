#!/usr/bin/env bash
# Nine-event parade. Skips blocked. NOT the room script.
# Room lead: docs/DEMO.md (90s). Table proof: scripts/demo_power.sh.
set -euo pipefail

HAL_URL="${HAL_URL:-http://127.0.0.1:5001}"

if ! curl -fsS "$HAL_URL/health" >/dev/null 2>&1 && ! curl -fsS "$HAL_URL/docs" >/dev/null 2>&1; then
  echo "HAL is not reachable at $HAL_URL; start HAL with: HAL_SIMULATE=1 uvicorn hal.server:app --host 127.0.0.1 --port 5001" >&2
  exit 1
fi

for event in started thinking waiting_for_user permission_required tests_passed tests_failed completed quiet; do
  echo "==> $event"
  agent-body post --event "$event" --mode focus --hal "$HAL_URL"
  sleep 1
 done
