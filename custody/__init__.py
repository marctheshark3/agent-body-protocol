"""Two-layer Lamp custody: possession and presence. Below the brain."""

from .gate import enforce
from .handoff import already_owned, handoff
from .presence import bind
from .receipts import ReceiptStore
from .record import CustodyRecord
from .refuse import REFUSE

__all__ = [
    "CustodyRecord",
    "ReceiptStore",
    "REFUSE",
    "already_owned",
    "bind",
    "enforce",
    "handoff",
]
