"""End-to-end smoke test against a running stack (`make up && make seed`).

Drives the bot the way WhatsApp would: signed webhooks in, stored replies out, through
the real API, Redis queue, worker and Postgres. Exits non-zero on the first failure.

    uv run python scripts/smoke_test.py [--url http://localhost:8000]
"""

import argparse
import json
import sys
import time
import uuid
from typing import Any, NoReturn

import httpx

from tee_concierge.config import get_settings
from tee_concierge.infrastructure.whatsapp.signature import sign
from tee_concierge.infrastructure.whatsapp.simulator import tap_payload, text_payload

PHONE = f"519{uuid.uuid4().int % 10**8:08d}"


class Smoke:
    def __init__(self, url: str) -> None:
        self.http = httpx.Client(base_url=url, timeout=10.0)
        self.secret = get_settings().whatsapp_app_secret.get_secret_value()
        self.last_id = 0

    def _post(self, payload: dict[str, Any], *, signature: str | None = None) -> httpx.Response:
        body = json.dumps(payload).encode()
        headers = {"X-Hub-Signature-256": signature or sign(self.secret, body)}
        return self.http.post("/webhook", content=body, headers=headers)

    def _replies(self, timeout: float = 15.0) -> list[dict[str, Any]]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found: list[dict[str, Any]] = self.http.get(
                f"/dev/outbox/{PHONE}", params={"after_id": self.last_id}
            ).json()
            if found:
                self.last_id = found[-1]["id"]
                return found
            time.sleep(0.3)
        fail("no reply within timeout (is the worker running?)")

    def say(self, text: str) -> dict[str, Any]:
        response = self._post(text_payload(PHONE, text, f"smoke.{uuid.uuid4().hex}"))
        check(response.status_code == 200, f"webhook returned {response.status_code}")
        return self._replies()[-1]

    def tap(self, reply: dict[str, Any], title_part: str) -> dict[str, Any]:
        option = next((o for o in reply["options"] if title_part in o["title"]), None)
        if option is None:
            fail(f"no option containing {title_part!r} in {reply['options']}")
        as_list = len(reply["options"]) > 3
        payload = tap_payload(
            PHONE, option["id"], option["title"], f"smoke.{uuid.uuid4().hex}", as_list=as_list
        )
        check(self._post(payload).status_code == 200, "tap webhook failed")
        return self._replies()[-1]


def fail(message: str) -> NoReturn:
    print(f"FAIL: {message}")
    sys.exit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def wait_for_health(url: str, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{url}/health", timeout=2.0).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    fail("API did not become healthy")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    url = parser.parse_args().url
    wait_for_health(url)
    smoke = Smoke(url)

    # 1. Security: unsigned webhooks are rejected.
    bad = smoke._post(text_payload(PHONE, "hola", "smoke.bad"), signature="sha256=00")
    check(bad.status_code == 401, "an unsigned webhook must be rejected with 401")
    print("ok  unsigned webhook rejected")

    # 2. Greeting opens the main menu.
    menu = smoke.say("Hola")
    check("Bienvenido" in menu["body"] and len(menu["options"]) >= 6, "main menu not shown")
    print("ok  'Hola' opens the main menu")

    # 3. Browse the catalog by tapping: category -> product -> sizes -> stock.
    categories = smoke.tap(menu, "catálogo")
    products = smoke.tap(categories, categories["options"][0]["title"])
    detail = smoke.tap(products, products["options"][0]["title"])
    check("S/ " in detail["body"], "product detail must show the price in soles")
    sizes = smoke.tap(detail, "Tallas")
    stock = smoke.tap(sizes, "Talla")
    check(
        "disponible" in stock["body"] or "agotado" in stock["body"] or "últimas" in stock["body"],
        "stock screen must show availability",
    )
    print("ok  catalog browsing: category > product > sizes > stock")

    # 3b. Typed codes: "3" is the third option of the main menu, from any screen.
    check("Envíos" in smoke.say("3")["body"], "typed code did not open its node")
    check("Bienvenido" in smoke.say("0")["body"], "code 0 must return to the main menu")
    print("ok  typed codes: '3' opens Envíos, '0' returns to the main menu")

    # 4. Free text: keyword shortcut and fallback.
    check(
        "Contáctanos" in smoke.say("quiero hablar con un asesor")["body"], "contact shortcut failed"
    )
    check(smoke.say("asdfgh")["body"].startswith("No te entendí"), "fallback message missing")
    print("ok  keyword shortcut and fallback")

    # 5. Idempotency: the same wamid delivered 3 times produces one reply.
    wamid = f"smoke.dup.{uuid.uuid4().hex}"
    for _ in range(3):
        check(smoke._post(text_payload(PHONE, "menu", wamid)).status_code == 200, "dup post failed")
    first = smoke._replies()
    time.sleep(3)  # give a (buggy) second job time to produce a duplicate
    extra = smoke.http.get(f"/dev/outbox/{PHONE}", params={"after_id": smoke.last_id}).json()
    check(
        len(first) == 1 and not extra,
        f"duplicate delivery produced {len(first) + len(extra)} replies",
    )
    print("ok  duplicate delivery answered once")

    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
