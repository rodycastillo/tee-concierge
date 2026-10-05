import time
from typing import Any


def _envelope(phone: str, name: str, message: dict[str, Any]) -> dict[str, Any]:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "FAKE_WABA",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "contacts": [{"wa_id": phone, "profile": {"name": name}}],
                            "messages": [
                                {
                                    "from": phone,
                                    "timestamp": str(int(time.time())),
                                    **message,
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def text_payload(phone: str, text: str, wamid: str, name: str = "Cliente") -> dict[str, Any]:
    """A minimal Cloud API webhook payload for an inbound text message."""
    return _envelope(phone, name, {"id": wamid, "type": "text", "text": {"body": text}})


def tap_payload(
    phone: str, option_id: str, title: str, wamid: str, *, as_list: bool, name: str = "Cliente"
) -> dict[str, Any]:
    """Payload for a customer tapping a reply button or a list row."""
    kind = "list_reply" if as_list else "button_reply"
    return _envelope(
        phone,
        name,
        {
            "id": wamid,
            "type": "interactive",
            "interactive": {"type": kind, kind: {"id": option_id, "title": title}},
        },
    )
