#!/usr/bin/env bash
# 6. USB-C — take it with you (no Call Sam).
# Unplug it and take it with you.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"

echo "==> Unplug it and take it with you."
python3 -m mapper.agent_body power --sim battery --record /tmp/power-walk.json
