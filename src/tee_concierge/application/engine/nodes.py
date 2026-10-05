from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass

from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.routing import normalize
from tee_concierge.domain.messaging import Reply
from tee_concierge.domain.ports import CatalogRepository, FaqRepository


@dataclass(frozen=True, slots=True)
class NodeContext:
    """Everything a node needs to render."""

    store: StoreInfo
    catalog: CatalogRepository
    faq: FaqRepository
    args: tuple[str, ...] = ()
    profile_name: str | None = None


NodeHandler = Callable[[NodeContext], Awaitable[Reply]]


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    parent: str | None
    handler: NodeHandler
    keywords: tuple[str, ...] = ()


class NodeRegistry:
    """The declarative menu tree. Adding a menu entry means registering a node."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}

    def register(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError(f"duplicate node id: {node.id}")
        self._nodes[node.id] = node

    def get(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def __iter__(self) -> Iterator[Node]:
        return iter(self._nodes.values())

    def match_keyword(self, text: str) -> Node | None:
        """First node (in registration order) with a keyword or phrase in `text`."""
        padded = f" {normalize(text)} "
        for node in self._nodes.values():
            if any(f" {normalize(k)} " in padded for k in node.keywords):
                return node
        return None
