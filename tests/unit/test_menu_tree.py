"""Structural checks over the whole menu, including the data-driven catalog screens:
no dead ends, no broken links, WhatsApp limits hold on every screen the demo data can produce."""

from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.menu import build_registry
from tee_concierge.application.engine.nav import CONTACT, MAIN
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import decode
from tests.fakes import InMemoryCatalog, InMemoryFaq

STORE = StoreInfo(name="Tee Concierge", contact_phone="51943713293", hours="Lun a Sáb")


def _ctx(args: tuple[str, ...] = ()) -> NodeContext:
    return NodeContext(STORE, InMemoryCatalog(), InMemoryFaq(), args, profile_name="Ana")


async def test_walk_every_screen_reachable_from_main() -> None:
    registry = build_registry()
    seen_options: set[str] = set()
    visited_nodes: set[str] = set()
    pending = ["go:main"]

    while pending:
        option_id = pending.pop()
        if option_id in seen_options:
            continue
        seen_options.add(option_id)
        route = decode(option_id)
        assert route is not None, f"bad option id {option_id!r}"
        node = registry.get(route.node)
        assert node is not None, f"link to missing node {route.node!r} ({option_id})"
        visited_nodes.add(route.node)

        reply = await node.handler(_ctx(route.args))  # building the Reply validates WhatsApp limits

        assert reply.options, f"{option_id} is a dead end"
        pending.extend(o.id for o in reply.options)

    assert visited_nodes == {n.id for n in registry}, "orphan nodes unreachable from main"
    assert len(seen_options) > 40  # categories x pages x products x sizes were really explored


async def test_every_screen_can_reach_the_main_menu() -> None:
    registry = build_registry()
    pending, seen = ["go:main"], set()
    while pending:
        option_id = pending.pop()
        if option_id in seen:
            continue
        seen.add(option_id)
        route = decode(option_id)
        assert route is not None
        node = registry.get(route.node)
        assert node is not None
        reply = await node.handler(_ctx(route.args))
        targets = {decode(o.id).node for o in reply.options}  # type: ignore[union-attr]
        assert MAIN in targets or route.node == MAIN, f"{option_id} has no way back to the menu"
        pending.extend(o.id for o in reply.options)


async def test_static_screens_offer_contact() -> None:
    registry = build_registry()
    for node_id in ("sizes", "shipping", "payment", "returns", "hours", "catalog"):
        node = registry.get(node_id)
        assert node is not None
        reply = await node.handler(_ctx())
        assert CONTACT in {decode(o.id).node for o in reply.options}, node_id  # type: ignore[union-attr]
