"""`tee-chat`: talk to the bot from the terminal using the fake WhatsApp gateway.

It posts signed Cloud-API-shaped webhooks to the local API and prints the
replies the bot stored, so the whole pipeline runs without a Meta account.
"""

import argparse
import json
import time
import uuid

import httpx

from tee_concierge.config import get_settings
from tee_concierge.infrastructure.whatsapp.signature import sign
from tee_concierge.infrastructure.whatsapp.simulator import text_payload


def _send(client: httpx.Client, secret: str, phone: str, text: str) -> None:
    body = json.dumps(text_payload(phone, text, f"fake.in.{uuid.uuid4().hex}")).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Hub-Signature-256": sign(secret, body), "Content-Type": "application/json"},
    )
    response.raise_for_status()


def _wait_for_replies(
    client: httpx.Client, phone: str, after_id: int, timeout: float
) -> list[dict]:  # type: ignore[type-arg]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        replies = client.get(f"/dev/outbox/{phone}", params={"after_id": after_id}).json()
        if replies:
            return list(replies)
        time.sleep(0.3)
    return []


def main() -> None:
    parser = argparse.ArgumentParser(prog="tee-chat", description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--phone", default="51999999999")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    secret = get_settings().whatsapp_app_secret.get_secret_value()
    last_id = 0
    with httpx.Client(base_url=args.url, timeout=10.0) as client:
        print(f"Chatting as {args.phone}. Ctrl+C to quit.")
        try:
            while True:
                text = input("tú> ").strip()
                if not text:
                    continue
                _send(client, secret, args.phone, text)
                replies = _wait_for_replies(client, args.phone, last_id, args.timeout)
                if not replies:
                    print("(no reply, is the worker running?)")
                for reply in replies:
                    print(f"bot> {reply['body']}")
                    last_id = max(last_id, reply["id"])
        except (KeyboardInterrupt, EOFError):
            print()


if __name__ == "__main__":
    main()
