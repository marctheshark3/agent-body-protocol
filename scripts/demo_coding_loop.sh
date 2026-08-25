#!/usr/bin/env bash
# 1. Coding loop — body, not a log.
# You should not have to watch a log. Think, stuck, fail, pass, done — you can see it from across the desk.
# Adapter/fake-hook path (same as demo_room.sh). Not typed agent_body post.
# completed stays happy_wiggle. Hatch is script #5, not this done beat.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
MAPPER="${MAPPER:-http://127.0.0.1:5051/event}"
BEAT="${BEAT:-4}"
HOOK=(python3 adapters/claude-code/hook.py --mapper "$MAPPER")

beat() {
  local hook="$1"
  local payload="$2"
  echo "==> $3"
  printf '%s\n' "$payload" | "${HOOK[@]}" --hook "$hook"
  sleep "$BEAT"
}

beat PostToolUse '{}' "It thinks."
beat Notification '{}' "It looks at you."
beat Stop '{"result":"3 failed"}' "It failed."
beat Stop '{"result":"tests passed, 0 failed"}' "It passed."
beat Stop '{"result":"done"}' "done"
