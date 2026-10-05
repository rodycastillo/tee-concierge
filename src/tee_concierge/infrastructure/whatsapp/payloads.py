from typing import Any

from tee_concierge.domain.messaging import Reply, ReplyKind

LIST_SECTION_TITLE = "Opciones"


def build_send_payload(to: str, reply: Reply) -> dict[str, Any]:
    """Cloud API `messages` request body for a text, buttons or list reply."""
    base: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
    }
    kind = reply.kind
    if kind is ReplyKind.TEXT:
        return {**base, "type": "text", "text": {"body": reply.body, "preview_url": False}}

    interactive: dict[str, Any] = {"body": {"text": reply.body}}
    if kind is ReplyKind.BUTTONS:
        interactive["type"] = "button"
        interactive["action"] = {
            "buttons": [
                {"type": "reply", "reply": {"id": o.id, "title": o.title}} for o in reply.options
            ]
        }
    else:
        rows = []
        for o in reply.options:
            row: dict[str, str] = {"id": o.id, "title": o.title}
            if o.description:
                row["description"] = o.description
            rows.append(row)
        interactive["type"] = "list"
        interactive["action"] = {
            "button": reply.list_button,
            "sections": [{"title": LIST_SECTION_TITLE, "rows": rows}],
        }
    return {**base, "type": "interactive", "interactive": interactive}
