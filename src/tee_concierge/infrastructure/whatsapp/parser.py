from datetime import UTC, datetime
from typing import Any

from tee_concierge.domain.messaging import InboundMessage, MessageType


def parse_inbound_messages(payload: dict[str, Any]) -> list[InboundMessage]:
    """Extract customer messages from a Cloud API webhook payload.

    Status callbacks (sent/delivered/read) and malformed entries are skipped.
    """
    messages: list[InboundMessage] = []
    for entry in _as_list(payload.get("entry")):
        for change in _as_list(_as_dict(entry).get("changes")):
            value = _as_dict(_as_dict(change).get("value"))
            names = {
                c.get("wa_id"): _as_dict(c.get("profile")).get("name")
                for c in map(_as_dict, _as_list(value.get("contacts")))
            }
            for raw in map(_as_dict, _as_list(value.get("messages"))):
                parsed = _parse_one(raw, names)
                if parsed is not None:
                    messages.append(parsed)
    return messages


def _parse_one(raw: dict[str, Any], names: dict[Any, Any]) -> InboundMessage | None:
    wamid, phone = raw.get("id"), raw.get("from")
    if not isinstance(wamid, str) or not isinstance(phone, str):
        return None
    kind = raw.get("type")
    text: str | None = None
    reply_id: str | None = None
    msg_type = MessageType.UNSUPPORTED
    if kind == "text":
        msg_type, text = MessageType.TEXT, _as_dict(raw.get("text")).get("body")
    elif kind == "interactive":
        interactive = _as_dict(raw.get("interactive"))
        subtype = interactive.get("type")
        if subtype in ("button_reply", "list_reply"):
            reply = _as_dict(interactive.get(subtype))
            msg_type = MessageType(subtype)
            reply_id, text = reply.get("id"), reply.get("title")
    return InboundMessage(
        wamid=wamid,
        phone=phone,
        type=msg_type,
        sent_at=_parse_timestamp(raw.get("timestamp")),
        text=text,
        reply_id=reply_id,
        profile_name=names.get(phone),
    )


def _parse_timestamp(value: Any) -> datetime:
    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError):
        return datetime.now(UTC)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
