"""F1: claim the body. Installer face and setup phrase die here."""

from __future__ import annotations

from datetime import datetime, timezone

from .record import CustodyRecord


class AlreadyOwned(ValueError):
    """Second handoff while an owner exists."""


def already_owned(record: CustodyRecord) -> bool:
    return bool(record.owner)


def handoff(
    record: CustodyRecord,
    *,
    owner: str,
    owner_face: str,
    owner_phrase: str | None = None,
    installer_faces: list[str] | None = None,
    setup_phrase: str | None = None,
    when: str | None = None,
) -> CustodyRecord:
    del setup_phrase  # setup phrases never survive F1
    if already_owned(record):
        raise AlreadyOwned("body already has an owner")
    expired = installer_faces or []
    if record.bindable_faces:
        expired = list(dict.fromkeys([*expired, *record.bindable_faces]))
    record.owner = owner
    record.installer_expired_at = when or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record.bindable_faces = [owner_face]
    record.expired_installer_faces = expired
    record.owner_phrase = owner_phrase
    record.leftover_closed = True
    return record
