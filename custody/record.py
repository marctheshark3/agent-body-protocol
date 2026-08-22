"""On-disk possession record. Not GET /face/owners."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Live Autonomous OS bootstrap reads this after F1.
DEFAULT_LIVE_PATH = Path("/var/lib/lamp/custody.json")


@dataclass
class CustodyRecord:
    owner: str | None = None
    installer_expired_at: str | None = None
    bindable_faces: list[str] = field(default_factory=list)
    expired_installer_faces: list[str] = field(default_factory=list)
    owner_phrase: str | None = None
    leftover_closed: bool = False
    revoked_buddy_tokens: list[str] = field(default_factory=list)
    ota_frozen: bool = False
    last_applied: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CustodyRecord:
        return cls(
            owner=data.get("owner"),
            installer_expired_at=data.get("installer_expired_at"),
            bindable_faces=list(data.get("bindable_faces") or []),
            expired_installer_faces=list(data.get("expired_installer_faces") or []),
            owner_phrase=data.get("owner_phrase"),
            leftover_closed=bool(data.get("leftover_closed", False)),
            revoked_buddy_tokens=list(data.get("revoked_buddy_tokens") or []),
            ota_frozen=bool(data.get("ota_frozen", False)),
            last_applied=data.get("last_applied"),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2, sort_keys=True) + "\n")

    @classmethod
    def load(cls, path: Path) -> CustodyRecord:
        if not path.exists():
            return cls()
        return cls.from_json(json.loads(path.read_text()))
