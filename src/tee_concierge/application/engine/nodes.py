from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass

from tee_concierge.application.content.messages import Messages
from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.routing import normalize, normalize_code
from tee_concierge.domain.messaging import Reply
from tee_concierge.domain.ports import CatalogRepository


@dataclass(frozen=True, slots=True)
class NavTargets:
    """Ids of the special nodes screens link to (None when the business has none)."""

    contact: str | None = None
    catalog: str | None = None


@dataclass(frozen=True, slots=True)
class NodeContext:
    """Everything a node needs to render."""

    business: StoreInfo
    catalog: CatalogRepository
    messages: Messages
    nav: NavTargets
    args: tuple[str, ...] = ()
    profile_name: str | None = None


NodeHandler = Callable[[NodeContext], Awaitable[Reply]]


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    parent: str | None
    handler: NodeHandler
    code: str | None = None  # typed shortcut, global across the menu
    keywords: tuple[str, ...] = ()


class NodeRegistry:
    """The menu tree, built from the business's config."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._by_code: dict[str, Node] = {}

    def register(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError(f"duplicate node id: {node.id}")
        self._nodes[node.id] = node
        if node.code is not None:
            code = normalize_code(node.code)
            if code in self._by_code:
                raise ValueError(f"duplicate code: {node.code}")
            self._by_code[code] = node

    def get(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def by_code(self, typed: str) -> Node | None:
        return self._by_code.get(normalize_code(typed))

    def __iter__(self) -> Iterator[Node]:
        return iter(self._nodes.values())

    def match_keyword(self, text: str) -> Node | None:
        """First node (in registration order) with a keyword or phrase in `text`."""
        padded = f" {normalize(text)} "
        for node in self._nodes.values():
            if any(f" {normalize(k)} " in padded for k in node.keywords):
                return node
        return None
