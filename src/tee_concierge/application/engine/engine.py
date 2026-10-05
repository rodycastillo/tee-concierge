from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import structlog

from tee_concierge.application.content import es
from tee_concierge.application.content.store import StoreInfo
from tee_concierge.application.engine.menu import CONTACT, MAIN, build_registry
from tee_concierge.application.engine.nodes import NodeContext, NodeRegistry
from tee_concierge.application.engine.routing import decode, encode
from tee_concierge.domain.messaging import (
    ConversationState,
    InboundMessage,
    MessageType,
    Option,
    Reply,
)
from tee_concierge.domain.ports import ConversationRepository

log = structlog.get_logger()

SESSION_TIMEOUT = timedelta(hours=2)
FAILURES_BEFORE_CONTACT = 2


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MenuEngine:
    """Turns an inbound message into the next menu screen.

    Resolution order: tapped option, then keyword shortcut, then fallback that
    re-shows the current menu. A new session (first message, or after
    `SESSION_TIMEOUT` of silence) always starts at the main menu.
    """

    def __init__(
        self,
        conversations: ConversationRepository,
        store: StoreInfo,
        registry: NodeRegistry | None = None,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._conversations = conversations
        self._store = store
        self._registry = registry or build_registry()
        self._clock = clock

    async def reply_to(self, message: InboundMessage) -> Reply:
        now = self._clock()
        state = await self._conversations.get(message.phone)
        new_session = (
            state is None or state.updated_at is None or now - state.updated_at > SESSION_TIMEOUT
        )
        if state is None or new_session:
            state = ConversationState(phone=message.phone)

        node_id, failures, reply = await self._resolve(message, state, new_session)
        await self._conversations.save(
            ConversationState(message.phone, node=node_id, failures=failures, updated_at=now)
        )
        return reply

    async def _resolve(
        self, message: InboundMessage, state: ConversationState, new_session: bool
    ) -> tuple[str, int, Reply]:
        if message.reply_id:
            route = decode(message.reply_id)
            if route and self._registry.get(route.node):
                return route.node, 0, await self._render(route.node, message, route.args)
            log.info("stale_option_id", option_id=message.reply_id)
            return MAIN, 0, await self._render(MAIN, message)

        if new_session:
            return MAIN, 0, await self._render(MAIN, message)

        text = message.text if message.type is MessageType.TEXT else None
        if text is None:
            return await self._fallback(message, state, es.UNSUPPORTED, count_failure=False)

        node = self._registry.match_keyword(text)
        if node is not None:
            return node.id, 0, await self._render(node.id, message)
        return await self._fallback(message, state, es.NOT_UNDERSTOOD, count_failure=True)

    async def _fallback(
        self, message: InboundMessage, state: ConversationState, prefix: str, *, count_failure: bool
    ) -> tuple[str, int, Reply]:
        failures = state.failures + (1 if count_failure else 0)
        if failures >= FAILURES_BEFORE_CONTACT:
            reply = Reply(
                es.NOT_UNDERSTOOD_TWICE,
                (
                    Option(encode(CONTACT), es.LABEL_CONTACT),
                    Option(encode(MAIN), es.LABEL_MAIN),
                ),
            )
            return state.node, failures, reply
        current = await self._render(state.node, message)
        body = f"{prefix}\n\n{current.body}"
        reply = Reply(body[:1024], current.options, current.list_button)
        return state.node, failures, reply

    async def _render(
        self, node_id: str, message: InboundMessage, args: tuple[str, ...] = ()
    ) -> Reply:
        node = self._registry.get(node_id)
        if node is None:  # state points at a node that no longer exists
            node = self._registry.get(MAIN)
        assert node is not None  # noqa: S101
        ctx = NodeContext(store=self._store, args=args, profile_name=message.profile_name)
        return await node.handler(ctx)
