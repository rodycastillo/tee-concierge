from typing import Any

from tee_concierge.domain.messaging import DeliveryStatus, MessageType
from tee_concierge.infrastructure.whatsapp.parser import (
    parse_inbound_messages,
    parse_statuses,
    parse_webhook,
)
from tee_concierge.infrastructure.whatsapp.simulator import text_payload


def _wrap(message: dict[str, Any]) -> dict[str, Any]:
    base = {"from": "51911111111", "timestamp": "1700000000", **message}
    return {"entry": [{"changes": [{"value": {"messages": [base]}}]}]}


def test_text_message() -> None:
    [msg] = parse_inbound_messages(text_payload("51911111111", "Hola", "wamid.1", name="Ana"))

    assert (msg.wamid, msg.phone, msg.type, msg.text) == (
        "wamid.1",
        "51911111111",
        MessageType.TEXT,
        "Hola",
    )
    assert msg.profile_name == "Ana"


def test_button_and_list_replies_carry_the_tapped_id() -> None:
    button = {
        "id": "w2",
        "type": "interactive",
        "interactive": {
            "type": "button_reply",
            "button_reply": {"id": "nav:back", "title": "Volver"},
        },
    }
    row = {
        "id": "w3",
        "type": "interactive",
        "interactive": {"type": "list_reply", "list_reply": {"id": "cat:12", "title": "Polos"}},
    }

    [b] = parse_inbound_messages(_wrap(button))
    [r] = parse_inbound_messages(_wrap(row))

    assert (b.type, b.reply_id, b.text) == (MessageType.BUTTON_REPLY, "nav:back", "Volver")
    assert (r.type, r.reply_id) == (MessageType.LIST_REPLY, "cat:12")


def test_unsupported_types_are_kept_so_the_bot_can_answer_politely() -> None:
    [msg] = parse_inbound_messages(_wrap({"id": "w4", "type": "audio", "audio": {"id": "x"}}))
    assert msg.type is MessageType.UNSUPPORTED


def test_status_callbacks_and_garbage_are_ignored() -> None:
    status = {"entry": [{"changes": [{"value": {"statuses": [{"id": "w", "status": "read"}]}}]}]}
    assert parse_inbound_messages(status) == []
    assert parse_inbound_messages({}) == []
    assert parse_inbound_messages({"entry": "nope"}) == []
    assert parse_inbound_messages(_wrap({"type": "text"}) | {"x": 1}) == []  # no id


def _statuses(*items: dict[str, Any]) -> dict[str, Any]:
    return {"entry": [{"changes": [{"value": {"statuses": list(items)}}]}]}


def test_delivery_receipts_are_parsed() -> None:
    payload = _statuses(
        {
            "id": "o1",
            "status": "delivered",
            "timestamp": "1700000000",
            "recipient_id": "51911111111",
        },
        {
            "id": "o2",
            "status": "failed",
            "errors": [{"code": 131047, "title": "Re-engagement message"}],
        },
        {"id": "o3", "status": "weird"},  # unknown status ignored
        {"status": "read"},  # no id ignored
    )

    first, second = parse_statuses(payload)

    assert (first.wamid, first.status) == ("o1", DeliveryStatus.DELIVERED)
    assert (second.status, second.error) == (DeliveryStatus.FAILED, "Re-engagement message")


def test_parse_webhook_separates_messages_from_statuses() -> None:
    parsed = parse_webhook(text_payload("51911111111", "Hola", "w1"))
    assert len(parsed.messages) == 1 and parsed.statuses == []
    only_status = parse_webhook(_statuses({"id": "o1", "status": "read"}))
    assert only_status.messages == [] and len(only_status.statuses) == 1
