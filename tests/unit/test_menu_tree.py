"""Structural checks over every example business: no dead ends, no broken links, WhatsApp
limits hold on every screen (including the data-driven catalog with the demo data)."""

from pathlib import Path

import pytest

from tee_concierge.application.engine.nav import MAIN
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import decode
from tee_concierge.application.menu.dryrun import dry_run
from tee_concierge.infrastructure.menu.loader import load_menu
from tests.fakes import InMemoryCatalog

EXAMPLES = sorted(Path("examples").glob("*/menu.yaml"))


def test_examples_are_found() -> None:
    assert {p.parent.name for p in EXAMPLES} >= {"tshirt-store", "dental-clinic"}


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.parent.name)
async def test_every_example_passes_the_dry_run(path: Path) -> None:
    assert await dry_run(load_menu(path), InMemoryCatalog()) == []


async def test_walk_every_catalog_screen_with_demo_data() -> None:
    menu = load_menu("examples/tshirt-store/menu.yaml")
    catalog = InMemoryCatalog()
    seen, pending, nodes = set[str](), ["go:main"], set[str]()
    while pending:
        option_id = pending.pop()
        if option_id in seen:
            continue
        seen.add(option_id)
        route = decode(option_id)
        assert route is not None, f"bad option id {option_id!r}"
        node = menu.registry.get(route.node)
        assert node is not None, f"link to missing node {route.node!r}"
        nodes.add(node.id)
        ctx = NodeContext(menu.business, catalog, menu.messages, menu.nav, route.args)
        reply = await node.handler(ctx)  # building the Reply validates WhatsApp limits
        assert reply.options, f"{option_id} is a dead end"
        targets = {r.node for o in reply.options if (r := decode(o.id))}
        assert MAIN in targets or node.id == MAIN, f"{option_id} cannot reach the main menu"
        pending.extend(o.id for o in reply.options)

    assert nodes == {n.id for n in menu.registry}, "orphan nodes unreachable from main"
    assert len(seen) > 40  # categories x pages x products x sizes were really explored


async def test_dry_run_reports_screens_that_cannot_render() -> None:
    from tee_concierge.application.menu.builder import build_menu
    from tee_concierge.application.menu.config import MenuConfig

    menu = build_menu(
        MenuConfig.model_validate(
            {
                "business": {"name": "Demo"},
                "menu": [{"id": "long", "type": "text", "title": "Largo", "body": "x" * 2000}],
            }
        )
    )

    errors = await dry_run(menu)

    assert any("'long' cannot be rendered" in e for e in errors)
