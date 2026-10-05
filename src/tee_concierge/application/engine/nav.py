from tee_concierge.application.content import es
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.messaging import Option

MAIN = "main"
CONTACT = "contact"


def go(node: str, label: str) -> Option:
    return Option(id=encode(node), title=label)


def navigation(parent: str | None) -> tuple[Option, ...]:
    """Footer for leaf screens. 'Volver' is omitted when it would equal 'Menú principal'."""
    options: list[Option] = []
    if parent not in (None, MAIN):
        options.append(go(parent, es.LABEL_BACK))
    options.append(go(MAIN, es.LABEL_MAIN))
    options.append(go(CONTACT, es.LABEL_CONTACT))
    return tuple(options)
