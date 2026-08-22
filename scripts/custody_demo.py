"""Judge ceremony. Two hosts required for F2. Fixtures only."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from custody.gate import enforce
from custody.handoff import handoff
from custody.leftover import CAMERA, LeftoverClient, LeftoverSurface
from custody.presence import bind
from custody.receipts import ReceiptStore
from custody.record import CustodyRecord
from custody.refuse import REFUSE
from custody.vendor import VENDOR_CAMERA, apply_update, freeze, pull
from custody.peer import accept as accept_peer

FAKE_OWNER = "Pat Demo"
FAKE_INSTALLER = "Riley Setup"
HOUSEHOLD = ("jenna", "mailloux")


def run(body_host: str, leftover_host: str, out: Path) -> dict:
    if leftover_host in {"", "127.0.0.1", "localhost"} or leftover_host == body_host:
        raise SystemExit("F2 requires CUSTODY_LEFTOVER_HOST distinct from the body")
    rec = CustodyRecord(bindable_faces=["riley-face"], owner_phrase="setup-phrase")
    rec = handoff(
        rec,
        owner=FAKE_OWNER,
        owner_face="pat-face",
        owner_phrase="oak-lamp",
        installer_faces=["riley-face"],
        setup_phrase="setup-phrase",
    )
    store = ReceiptStore(out / "receipts")
    store.issue("handoff", FAKE_OWNER, source="f1")
    surface = LeftoverSurface(body_host, leftover_host)
    surface.pair("installer-token")
    surface.close(rec)
    client = LeftoverClient(leftover_host, "installer-token")
    probe = surface.probe(client, CAMERA, store, rec)
    owner_turn = enforce({"v": 1, "event": "started", "ts": "2026-08-22T18:00:00Z"}, bind(rec, face="pat-face").subject)
    stranger_turn = enforce({"v": 1, "event": "started", "ts": "2026-08-22T18:00:00Z"}, bind(rec, face="crowd").subject)
    phrase = bind(rec, phrase="oak-lamp", camera_miss=True)
    applied = apply_update(rec, store, artifact="lamp-os-2", signed=True)
    leftover_after = surface.probe(client, CAMERA, store, rec)
    vendor_cam = pull(rec, store, VENDOR_CAMERA)
    peer_event = accept_peer(rec, store, kind="event", media="led", event="tests_passed")
    peer_cam = accept_peer(rec, store, kind="camera", media="ir")
    freeze(rec, "owner")
    frozen = apply_update(rec, store, artifact="lamp-os-3", signed=True)
    blob = json.dumps(store.list()).lower()
    for name in HOUSEHOLD:
        if name in blob:
            raise SystemExit("household PII leaked into receipts")
    return {
        "owner": rec.owner,
        "f2_ok": probe["ok"] is False,
        "owner_served": owner_turn.allowed,
        "stranger_refuse": stranger_turn.speech == REFUSE,
        "phrase_source": phrase.source,
        "signed_apply": applied["ok"] is True,
        "leftover_after_ota": leftover_after["ok"] is False,
        "vendor_camera_denied": vendor_cam["ok"] is False,
        "peer_event": peer_event["ok"] is True,
        "peer_camera_denied": peer_cam["ok"] is False,
        "frozen_refuse": frozen["ok"] is False,
        "receipts": store.list(),
        "installer": FAKE_INSTALLER,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lamp custody judge harness")
    parser.add_argument("--body-host", default=os.environ.get("CUSTODY_BODY_HOST", "10.0.0.8"))
    parser.add_argument("--leftover-host", default=os.environ.get("CUSTODY_LEFTOVER_HOST", ""))
    parser.add_argument("--out", default="var/custody-demo")
    args = parser.parse_args()
    result = run(args.body_host, args.leftover_host, Path(args.out))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
