#!/usr/bin/env bash
# Room 8–55s. Presenter stays quiet. Fake Claude hook is enough.
# Not demo_power.sh (table proof). Not demo.sh (nine-color parade).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
MAPPER="${MAPPER:-http://127.0.0.1:5051/event}"
BEAT="${BEAT:-6}"
HOOK=(python3 adapters/claude-code/hook.py --mapper "$MAPPER")

beat() {
  local hook="$1"
  local payload="$2"
  echo "==> $hook"
  printf '%s\n' "$payload" | "${HOOK[@]}" --hook "$hook"
  sleep "$BEAT"
}

consent() {
  local event="$1"
  python3 - "$MAPPER" "$event" <<'PY'
import json
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from mapper.hal_client import assert_hal_url

mapper = assert_hal_url(sys.argv[1])
event = {
    "v": 1,
    "event": sys.argv[2],
    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "source": "claude-code",
    "consent": "yes",
    "mode": "normal",
}
req = Request(
    mapper,
    data=json.dumps(event).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urlopen(req, timeout=2) as response:
    print(response.read().decode())
PY
}

echo "== 8-40s adapter loop"
beat PostToolUse '{}'
beat Notification '{}'
beat Stop '{"result":"3 failed"}'
beat Stop '{"result":"tests passed, 0 failed"}'
beat Stop '{"result":"done"}'

echo "== 40-55s Help Mode (real consent POST, not a fake nod)"
BEAT=4
beat PostToolUseFailure '{"error":"tool failed"}'
echo "==> consent yes"
consent thinking
sleep 4
echo "==> point reset"
consent waiting_for_user
