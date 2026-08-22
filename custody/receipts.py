"""Body-issued leftover deny receipts. Installer laptop is not the store."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Receipt:
    path: str
    when: str
    owner: str
    source: str | None = None

    def to_json(self) -> dict[str, Any]:
        data = {"path": self.path, "when": self.when, "owner": self.owner}
        if self.source:
            data["source"] = self.source
        return data


class ReceiptStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def issue(self, leftover_path: str, owner: str, *, source: str | None = None, when: str | None = None) -> Receipt | None:
        stamp = when or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        receipt = Receipt(leftover_path, stamp, owner, source)
        self._seq += 1
        dest = self.root / f"deny-{self._seq:04d}.json"
        try:
            dest.write_text(json.dumps(receipt.to_json(), indent=2, sort_keys=True) + "\n")
        except OSError:
            return None
        return receipt

    def list(self) -> list[dict[str, Any]]:
        out = []
        for file in sorted(self.root.glob("deny-*.json")):
            out.append(json.loads(file.read_text()))
        return out

    def delete_from(self, actor: str) -> bool:
        if actor != "body":
            return False
        for file in self.root.glob("deny-*.json"):
            file.unlink()
        return True
