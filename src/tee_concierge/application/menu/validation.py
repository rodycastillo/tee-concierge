"""Rules a menu file must satisfy, checked before it can reach a customer."""

import re
from collections.abc import Iterator

from tee_concierge.application.content.messages import Messages
from tee_concierge.application.engine.routing import normalize_code
from tee_concierge.application.menu.config import (
    CatalogNode,
    ContactNode,
    MenuConfig,
    MenuNode,
    NodeConfig,
    TextNode,
)

RESERVED_IDS = {"main", "cat", "product", "variants", "stock"}
MAIN_CODE = "0"
MAX_MAIN_CHILDREN = 10  # a list message holds 10 rows
MAX_SUBMENU_CHILDREN = 7  # leaves room for Volver, Menú principal, Contáctanos
_ID = re.compile(r"^[a-z0-9_-]{1,40}$")
_CODE = re.compile(r"^[a-z0-9._-]{1,20}$")


def iter_nodes(
    nodes: list[NodeConfig], parent: str = "main", prefix: str = ""
) -> Iterator[tuple[NodeConfig, str, str]]:
    """Depth-first: yields (node, parent id, auto code). Auto codes are positional: 1, 1.2, ..."""
    for position, node in enumerate(nodes, start=1):
        auto = f"{prefix}{position}"
        yield node, parent, auto
        if isinstance(node, MenuNode):
            yield from iter_nodes(node.children, node.id, f"{auto}.")


def resolve_codes(config: MenuConfig) -> dict[str, str]:
    """node id -> code (explicit if given, otherwise positional)."""
    return {n.id: n.code or auto for n, _parent, auto in iter_nodes(config.menu)}


def check_config(config: MenuConfig) -> list[str]:
    """Structural rules. Returns every problem found, so an owner can fix them in one pass."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_codes: dict[str, str] = {}
    codes = resolve_codes(config)

    for node, _parent, _auto in iter_nodes(config.menu):
        where = f"node '{node.id}'"
        if not _ID.match(node.id):
            errors.append(f"{where}: id must match [a-z0-9_-], max 40 chars")
        if node.id in RESERVED_IDS:
            errors.append(f"{where}: '{node.id}' is a reserved id")
        if node.id in seen_ids:
            errors.append(f"{where}: duplicate id")
        seen_ids.add(node.id)

        code = normalize_code(codes[node.id])
        if not _CODE.match(code):
            errors.append(f"{where}: code {codes[node.id]!r} must match [a-z0-9._-], max 20 chars")
        elif code == MAIN_CODE:
            errors.append(f"{where}: code '0' is reserved for the main menu")
        elif code in seen_codes:
            errors.append(f"{where}: code {code!r} already used by '{seen_codes[code]}'")
        seen_codes.setdefault(code, node.id)

        if not node.title.strip():
            errors.append(f"{where}: title must not be empty")
        if any(not k.strip() for k in node.keywords):
            errors.append(f"{where}: keywords must not be empty strings")
        if isinstance(node, MenuNode) and not node.children:
            errors.append(f"{where}: a menu needs at least one child")
        if isinstance(node, MenuNode) and len(node.children) > MAX_SUBMENU_CHILDREN:
            errors.append(
                f"{where}: {len(node.children)} children; a submenu allows at most "
                f"{MAX_SUBMENU_CHILDREN} (WhatsApp lists hold 10 rows, 3 are navigation)"
            )
        if (
            isinstance(node, TextNode)
            and node.image_url
            and not node.image_url.startswith("https://")
        ):
            errors.append(f"{where}: image_url must be an https URL")

    if not config.menu:
        errors.append("menu: needs at least one node")
    if len(config.menu) > MAX_MAIN_CHILDREN:
        errors.append(
            f"menu: {len(config.menu)} top-level nodes; the main menu allows {MAX_MAIN_CHILDREN}"
        )
    nodes = [n for n, _p, _a in iter_nodes(config.menu)]
    if sum(isinstance(n, CatalogNode) for n in nodes) > 1:
        errors.append("menu: at most one 'catalog' node is supported")
    if sum(isinstance(n, ContactNode) for n in nodes) > 1:
        errors.append("menu: at most one 'contact' node is supported")
    unknown = set(config.messages) - Messages.keys()
    if unknown:
        errors.append(f"messages: unknown keys {', '.join(sorted(unknown))}")
    return errors
