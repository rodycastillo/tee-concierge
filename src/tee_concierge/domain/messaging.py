from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class MessageType(StrEnum):
    TEXT = "text"
    BUTTON_REPLY = "button_reply"
    LIST_REPLY = "list_reply"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class InboundMessage:
    """A message received from a customer. `phone` is digits only (E.164 without '+')."""

    wamid: str
    phone: str
    type: MessageType
    sent_at: datetime
    text: str | None = None
    reply_id: str | None = None  # id of the tapped button or list row
    profile_name: str | None = None


@dataclass(frozen=True, slots=True)
class StoredReply:
    id: int
    body: str
    sent_at: datetime
