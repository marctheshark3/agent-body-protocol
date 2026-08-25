#!/usr/bin/env bash
# 6. USB-C — take it with you (no Call Sam).
# Unplug it and take it with you.
# Spoken/pantomime: unplug the cable and walk. This script does not unplug.
# A /tmp --record is not unplug-and-go. Do not pretend it is.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"

echo "==> Unplug it and take it with you."
echo "Spoken/pantomime: unplug USB-C and walk. Not a /tmp --record. Not a look-transfer."
