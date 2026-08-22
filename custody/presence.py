"""Face-first presence bind. Phrase is a labeled fallback, not a second owner."""

from __future__ import annotations

from dataclasses import dataclass

from .record import CustodyRecord

OWNER = "owner"
STRANGER = "stranger"
EXPIRED_INSTALLER = "expired-installer"


@dataclass(frozen=True)
class Presence:
    subject: str
    source: str


def bind(
    record: CustodyRecord,
    *,
    face: str | None = None,
    phrase: str | None = None,
    camera_miss: bool = False,
) -> Presence:
    if face:
        if record.owner and face in record.bindable_faces:
            return Presence(OWNER, "face")
        if face in record.expired_installer_faces:
            return Presence(EXPIRED_INSTALLER, "face")
        return Presence(STRANGER, "face")
    if camera_miss and phrase and record.owner_phrase and phrase == record.owner_phrase:
        return Presence(OWNER, "phrase-fallback")
    return Presence(STRANGER, "unbound")
