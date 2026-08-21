#!/usr/bin/env bash
set -euo pipefail

HAL_URL="${HAL_URL:-http://127.0.0.1:5001}"

if ! curl -fsS "$HAL_URL/health" >/dev/null 2>&1 && ! curl -fsS "$HAL_URL/docs" >/dev/null 2>&1; then
  echo "HAL is not reachable at $HAL_URL; start Autonomous OS with: make sim" >&2
  exit 1
fi

for event in started thinking waiting_for_user permission_required tests_passed tests_failed completed quiet; do
  echo "==> $event"
  agent-body post --event "$event" --mode focus --hal "$HAL_URL"
  sleep 1
 done
