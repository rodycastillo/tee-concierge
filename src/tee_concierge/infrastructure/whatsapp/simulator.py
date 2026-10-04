import time
from typing import Any


def text_payload(phone: str, text: str, wamid: str, name: str = "Cliente") -> dict[str, Any]:
    """A minimal Cloud API webhook payload for an inbound text message."""
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
                                    "id": wamid,
                                    "from": phone,
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
