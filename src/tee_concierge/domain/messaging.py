from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

# WhatsApp interactive message limits (Cloud API)
MAX_BUTTONS = 3
MAX_LIST_ROWS = 10
BODY_MAX = 1024
BUTTON_TITLE_MAX = 20
ROW_TITLE_MAX = 24
ROW_DESCRIPTION_MAX = 72
LIST_BUTTON_MAX = 20
OPTION_ID_MAX = 200


class MessageType(StrEnum):
    TEXT = "text"
    BUTTON_REPLY = "button_reply"
    LIST_REPLY = "list_reply"
    UNSUPPORTED = "unsupported"


class ReplyKind(StrEnum):
    TEXT = "text"
    BUTTONS = "buttons"
    LIST = "list"


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
class Option:
    """A tappable choice. `id` comes back as `reply_id` when the customer taps it."""

    id: str
    title: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class Reply:
    """What the bot says: a body plus optional options.

    No options -> plain text. Up to 3 options without descriptions -> reply
    buttons. Otherwise -> a list message (up to 10 rows). WhatsApp's limits are
    enforced here, so a menu that would be rejected by the API fails in tests.
    """

    body: str
    options: tuple[Option, ...] = ()
    list_button: str = "Ver opciones"
    image_url: str | None = None  # header image; WhatsApp allows it on button messages only

    @property
    def kind(self) -> ReplyKind:
        if not self.options:
            return ReplyKind.TEXT
        if len(self.options) <= MAX_BUTTONS and all(o.description is None for o in self.options):
            return ReplyKind.BUTTONS
        return ReplyKind.LIST

    def __post_init__(self) -> None:
        if not self.body or len(self.body) > BODY_MAX:
            raise ValueError(f"body must be 1..{BODY_MAX} chars, got {len(self.body)}")
        if len(self.options) > MAX_LIST_ROWS:
            raise ValueError(f"at most {MAX_LIST_ROWS} options, got {len(self.options)}")
        if len({o.id for o in self.options}) != len(self.options):
            raise ValueError("option ids must be unique")
        kind = self.kind
        title_max = BUTTON_TITLE_MAX if kind is ReplyKind.BUTTONS else ROW_TITLE_MAX
        for option in self.options:
            if not option.title or len(option.title) > title_max:
                raise ValueError(f"option title {option.title!r} must be 1..{title_max} chars")
            if len(option.id) > OPTION_ID_MAX:
                raise ValueError(f"option id too long: {option.id!r}")
            if option.description and len(option.description) > ROW_DESCRIPTION_MAX:
                raise ValueError(f"option description too long: {option.description!r}")
        if self.image_url and kind is not ReplyKind.BUTTONS:
            raise ValueError("image_url is only supported on button messages")
        if kind is ReplyKind.LIST and len(self.list_button) > LIST_BUTTON_MAX:
            raise ValueError(f"list_button must be at most {LIST_BUTTON_MAX} chars")


class DeliveryStatus(StrEnum):
    """Lifecycle of an outbound message. Order matters: statuses only move forward."""

    ACCEPTED = "accepted"  # the Cloud API took it
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

    @property
    def rank(self) -> int:
        return _STATUS_RANK[self]


_STATUS_RANK = {
    DeliveryStatus.ACCEPTED: 0,
    DeliveryStatus.SENT: 1,
    DeliveryStatus.DELIVERED: 2,
    DeliveryStatus.READ: 3,
    DeliveryStatus.FAILED: 1,
}


@dataclass(frozen=True, slots=True)
class StatusUpdate:
    wamid: str
    status: DeliveryStatus
    at: datetime
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedWebhook:
    messages: list[InboundMessage]
    statuses: list[StatusUpdate]


@dataclass(frozen=True, slots=True)
class HistoryMessage:
    id: int
    direction: str  # "in" | "out"
    type: str
    body: str | None
    status: str | None
    at: datetime


@dataclass(frozen=True, slots=True)
class StoredReply:
    id: int
    body: str
    options: tuple[Option, ...]
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class ConversationState:
    """Where a customer is in the menu. Option ids carry their own target, so this
    is only used to re-show the current menu and count misunderstandings."""

    phone: str
    node: str = "main"
    failures: int = 0
    updated_at: datetime | None = None
