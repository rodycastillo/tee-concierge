from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.messaging import Option

MAIN = "main"


def go(node: str, label: str) -> Option:
    return Option(id=encode(node), title=label)


def navigation(ctx: NodeContext, parent: str | None) -> tuple[Option, ...]:
    """Footer for screens. 'Volver' is omitted when it would equal 'Menú principal'."""
    options: list[Option] = []
    if parent is not None and parent != MAIN:
        options.append(go(parent, ctx.messages.label_back))
    options.append(go(MAIN, ctx.messages.label_main))
    if ctx.nav.contact and parent != ctx.nav.contact:
        options.append(go(ctx.nav.contact, ctx.messages.label_contact))
    return tuple(options)
