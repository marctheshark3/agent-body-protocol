"""Installer leftover double: Buddy token + LAN /hw/. Second host required."""

from __future__ import annotations

from dataclasses import dataclass, field

from .receipts import ReceiptStore
from .record import CustodyRecord

CAMERA = "leftover.camera"
MIC = "leftover.mic"
ACTUATE = "leftover.actuate"
BUDDY = "leftover.buddy"
HW = "leftover.hw"


@dataclass
class LeftoverClient:
    host: str
    token: str
    allowed: bool = True
    last_deny: str | None = None


@dataclass
class LeftoverSurface:
    body_host: str
    leftover_host: str
    tokens: dict[str, bool] = field(default_factory=dict)
    hw_open: bool = True

    def pair(self, token: str) -> None:
        self.tokens[token] = True

    def close(self, record: CustodyRecord) -> None:
        for token in list(self.tokens):
            self.tokens[token] = False
            if token not in record.revoked_buddy_tokens:
                record.revoked_buddy_tokens.append(token)
        self.hw_open = False
        record.leftover_closed = True

    def probe(self, client: LeftoverClient, channel: str, store: ReceiptStore, record: CustodyRecord) -> dict:
        if client.host == self.body_host:
            return {"ok": False, "error": "same-host-not-f2"}
        closed = record.leftover_closed or not self.hw_open or not self.tokens.get(client.token, False)
        if not closed:
            return {"ok": True, "channel": channel}
        owner = record.owner or "unknown"
        receipt = store.issue(channel, owner)
        client.last_deny = channel
        return {"ok": False, "channel": channel, "receipt": None if receipt is None else receipt.to_json()}
