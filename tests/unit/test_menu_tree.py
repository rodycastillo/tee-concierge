"""Structural checks over the whole menu: no dead ends, no broken links, WhatsApp limits hold."""

from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.menu import MAIN, build_registry
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import decode

STORE = StoreInfo(name="Tee Concierge", contact_phone="51943713293", hours="Lun a Sáb")


async def test_every_node_renders_with_valid_options_and_no_dead_end() -> None:
    registry = build_registry()
    reachable: set[str] = set()
    pending = [MAIN]

    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        node = registry.get(node_id)
        assert node is not None, f"link to missing node {node_id!r}"

        reply = await node.handler(
            NodeContext(store=STORE, profile_name="Ana")
        )  # builds Reply -> limits validated

        assert reply.options, f"node {node_id!r} is a dead end"
        for option in reply.options:
            route = decode(option.id)
            assert route is not None, f"{node_id}: bad option id {option.id!r}"
            pending.append(route.node)

    assert reachable == {node.id for node in registry}, "orphan nodes not reachable from main"


async def test_every_leaf_can_reach_main_and_contact() -> None:
    registry = build_registry()
    for node in registry:
        if node.id == MAIN:
            continue
        reply = await node.handler(NodeContext(store=STORE))
        targets = {decode(o.id).node for o in reply.options}  # type: ignore[union-attr]
        assert MAIN in targets, f"{node.id} has no way back to the main menu"
        if node.id != "contact":
            assert "contact" in targets, f"{node.id} has no 'Contáctanos'"
