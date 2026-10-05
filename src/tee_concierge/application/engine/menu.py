"""The menu tree: which nodes exist, how they link, and which words jump to them."""

from tee_concierge.application.content import es
from tee_concierge.application.engine.nodes import Node, NodeContext, NodeHandler, NodeRegistry
from tee_concierge.application.engine.routing import encode
from tee_concierge.domain.messaging import Option, Reply

MAIN = "main"
CONTACT = "contact"


def _go(node: str, label: str) -> Option:
    return Option(id=encode(node), title=label)


def navigation(parent: str | None) -> tuple[Option, ...]:
    """Footer for leaf screens. 'Volver' is omitted when it would equal 'Menú principal'."""
    options: list[Option] = []
    if parent not in (None, MAIN):
        options.append(_go(parent, es.LABEL_BACK))
    options.append(_go(MAIN, es.LABEL_MAIN))
    options.append(_go(CONTACT, es.LABEL_CONTACT))
    return tuple(options)


def _leaf(parent: str, text: str) -> NodeHandler:
    async def handler(ctx: NodeContext) -> Reply:
        return Reply(text, navigation(parent))

    return handler


async def _main(ctx: NodeContext) -> Reply:
    first_name = ctx.profile_name.split()[0][:30] if ctx.profile_name else None
    return Reply(
        es.welcome(ctx.store, first_name),
        (
            _go("catalog", es.LABEL_CATALOG),
            _go("sizes", es.LABEL_SIZES),
            _go("shipping", es.LABEL_SHIPPING),
            _go("payment", es.LABEL_PAYMENT),
            _go("returns", es.LABEL_RETURNS),
            _go("hours", es.LABEL_HOURS),
            _go(CONTACT, es.LABEL_CONTACT),
        ),
        list_button=es.LIST_BUTTON,
    )


async def _hours(ctx: NodeContext) -> Reply:
    return Reply(es.hours(ctx.store), navigation(MAIN))


async def _contact(ctx: NodeContext) -> Reply:
    return Reply(es.contact(ctx.store), (_go(MAIN, es.LABEL_MAIN),))


def build_registry() -> NodeRegistry:
    registry = NodeRegistry()
    # Order matters for keyword matching: the first matching node wins.
    registry.register(
        Node(
            CONTACT,
            MAIN,
            _contact,
            (
                "contacto",
                "contactar",
                "contactanos",
                "asesor",
                "humano",
                "persona",
                "llamar",
                "telefono",
                "numero",
                "hablar",
            ),
        )
    )
    registry.register(Node("sizes", MAIN, _leaf(MAIN, es.SIZES), ("talla", "tallas", "medidas")))
    registry.register(
        Node(
            "shipping",
            MAIN,
            _leaf(MAIN, es.SHIPPING),
            ("envio", "envios", "delivery", "despacho", "flete", "entrega"),
        )
    )
    registry.register(
        Node(
            "payment",
            MAIN,
            _leaf(MAIN, es.PAYMENT),
            ("pago", "pagos", "pagar", "yape", "plin", "transferencia", "tarjeta"),
        )
    )
    registry.register(
        Node(
            "returns",
            MAIN,
            _leaf(MAIN, es.RETURNS),
            ("cambio", "cambios", "devolucion", "devoluciones", "reembolso"),
        )
    )
    registry.register(
        Node(
            "hours",
            MAIN,
            _hours,
            ("horario", "horarios", "ubicacion", "direccion", "donde", "atienden", "abierto"),
        )
    )
    registry.register(
        Node(
            "catalog",
            MAIN,
            _leaf(MAIN, es.CATALOG),
            ("catalogo", "productos", "polos", "polo", "camisetas", "precio", "precios"),
        )
    )
    registry.register(
        Node(
            MAIN,
            None,
            _main,
            (
                "menu",
                "inicio",
                "hola",
                "holi",
                "buenas",
                "buenos dias",
                "buenas tardes",
                "buenas noches",
                "ayuda",
                "hello",
                "hi",
            ),
        )
    )
    return registry
