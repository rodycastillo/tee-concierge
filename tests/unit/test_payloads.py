from tee_concierge.domain.messaging import Option, Reply
from tee_concierge.infrastructure.whatsapp.payloads import build_send_payload


def test_text_payload() -> None:
    payload = build_send_payload("5191", Reply("hola"))
    assert payload["type"] == "text" and payload["text"]["body"] == "hola"


def test_button_payload() -> None:
    payload = build_send_payload(
        "5191", Reply("¿Seguimos?", (Option("go:a", "Sí"), Option("go:b", "No")))
    )
    interactive = payload["interactive"]
    assert interactive["type"] == "button"
    assert interactive["action"]["buttons"][0] == {
        "type": "reply",
        "reply": {"id": "go:a", "title": "Sí"},
    }


def test_list_payload() -> None:
    options = tuple(Option(f"go:{i}", f"Op {i}") for i in range(5))
    payload = build_send_payload("5191", Reply("Menú", options, list_button="Ver"))
    interactive = payload["interactive"]
    assert interactive["type"] == "list"
    assert interactive["action"]["button"] == "Ver"
    assert len(interactive["action"]["sections"][0]["rows"]) == 5


def test_button_payload_includes_the_image_header() -> None:
    reply = Reply("Polo", (Option("go:a", "Ver"),), image_url="https://example.com/a.jpg")
    interactive = build_send_payload("5191", reply)["interactive"]
    assert interactive["header"] == {
        "type": "image",
        "image": {"link": "https://example.com/a.jpg"},
    }
