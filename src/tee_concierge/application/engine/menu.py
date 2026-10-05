"""The menu tree: which nodes exist, how they link, and which words jump to them."""

from tee_concierge.application.content import es
from tee_concierge.application.engine import catalog_nodes
from tee_concierge.application.engine.nav import CONTACT, MAIN, go, navigation
from tee_concierge.application.engine.nodes import Node, NodeContext, NodeHandler, NodeRegistry
from tee_concierge.domain.messaging import Reply


def _faq(topic: str, default: str) -> NodeHandler:
    """A leaf whose text is editable in the database (`faq_entries`), with a default."""

    async def handler(ctx: NodeContext) -> Reply:
        return Reply(await ctx.faq.get(topic) or default, navigation(MAIN))

    return handler


async def _main(ctx: NodeContext) -> Reply:
    first_name = ctx.profile_name.split()[0][:30] if ctx.profile_name else None
    return Reply(
        es.welcome(ctx.store, first_name),
        (
            go(catalog_nodes.CATALOG, es.LABEL_CATALOG),
            go("sizes", es.LABEL_SIZES),
            go("shipping", es.LABEL_SHIPPING),
            go("payment", es.LABEL_PAYMENT),
            go("returns", es.LABEL_RETURNS),
            go("hours", es.LABEL_HOURS),
            go(CONTACT, es.LABEL_CONTACT),
        ),
        list_button=es.LIST_BUTTON,
    )


async def _hours(ctx: NodeContext) -> Reply:
    return Reply(es.hours(ctx.store), navigation(MAIN))


async def _contact(ctx: NodeContext) -> Reply:
    return Reply(es.contact(ctx.store), (go(MAIN, es.LABEL_MAIN),))


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
    registry.register(Node("sizes", MAIN, _faq("sizes", es.SIZES), ("talla", "tallas", "medidas")))
    registry.register(
        Node(
            "shipping",
            MAIN,
            _faq("shipping", es.SHIPPING),
            ("envio", "envios", "delivery", "despacho", "flete", "entrega"),
        )
    )
    registry.register(
        Node(
            "payment",
            MAIN,
            _faq("payment", es.PAYMENT),
            ("pago", "pagos", "pagar", "yape", "plin", "transferencia", "tarjeta"),
        )
    )
    registry.register(
        Node(
            "returns",
            MAIN,
            _faq("returns", es.RETURNS),
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
            catalog_nodes.CATALOG,
            MAIN,
            catalog_nodes.catalog,
            ("catalogo", "productos", "polos", "polo", "camisetas", "precio", "precios"),
        )
    )
    # Reachable only by tapping (no keywords): they need arguments.
    registry.register(Node(catalog_nodes.CATEGORY, catalog_nodes.CATALOG, catalog_nodes.category))
    registry.register(Node(catalog_nodes.PRODUCT, catalog_nodes.CATALOG, catalog_nodes.product))
    registry.register(Node(catalog_nodes.SIZES, catalog_nodes.CATALOG, catalog_nodes.sizes))
    registry.register(Node(catalog_nodes.STOCK, catalog_nodes.CATALOG, catalog_nodes.stock))
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
