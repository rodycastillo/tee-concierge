"""`tee-chat`: talk to the bot from the terminal using the fake WhatsApp gateway.

It posts signed Cloud-API-shaped webhooks to the local API and prints the
replies the bot stored. Type a number to tap an option, or any text.
"""

import argparse
import json
import time
import uuid
from typing import Any

import httpx

from tee_concierge.config import get_settings
from tee_concierge.domain.messaging import MAX_BUTTONS
from tee_concierge.infrastructure.whatsapp.signature import sign
from tee_concierge.infrastructure.whatsapp.simulator import tap_payload, text_payload

Option = dict[str, str]


def _post(client: httpx.Client, secret: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Hub-Signature-256": sign(secret, body), "Content-Type": "application/json"},
    )
    response.raise_for_status()


def _wait_for_replies(
    client: httpx.Client, phone: str, after_id: int, timeout: float
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        replies: list[dict[str, Any]] = client.get(
            f"/dev/outbox/{phone}", params={"after_id": after_id}
        ).json()
        if replies:
            return replies
        time.sleep(0.3)
    return []


def _print_reply(reply: dict[str, Any]) -> None:
    print(f"\nbot> {reply['body']}")
    for number, option in enumerate(reply["options"], start=1):
        print(f"      [{number}] {option['title']}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tee-chat", description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--phone", default="51999999999")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    secret = get_settings().whatsapp_app_secret.get_secret_value()
    last_id = 0
    options: list[Option] = []
    with httpx.Client(base_url=args.url, timeout=10.0) as client:
        print(f"Chatting as {args.phone}. Type text or an option number. Ctrl+C to quit.")
        try:
            while True:
                text = input("\ntú> ").strip()
                if not text:
                    continue
                wamid = f"fake.in.{uuid.uuid4().hex}"
                if text.isdigit() and 1 <= int(text) <= len(options):
                    chosen = options[int(text) - 1]
                    payload = tap_payload(
                        args.phone,
                        chosen["id"],
                        chosen["title"],
                        wamid,
                        as_list=len(options) > MAX_BUTTONS,
                    )
                else:
                    payload = text_payload(args.phone, text, wamid)
                _post(client, secret, payload)
                replies = _wait_for_replies(client, args.phone, last_id, args.timeout)
                if not replies:
                    print("(no reply, is the worker running?)")
                for reply in replies:
                    _print_reply(reply)
                    last_id = max(last_id, reply["id"])
                    options = reply["options"]
        except (KeyboardInterrupt, EOFError):
            print()


if __name__ == "__main__":
    main()
