from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import structlog

from tee_concierge.application.engine.nav import MAIN
from tee_concierge.application.engine.nodes import NodeContext
from tee_concierge.application.engine.routing import decode, encode
from tee_concierge.application.menu.builder import Menu
from tee_concierge.domain.messaging import (
    ConversationState,
    InboundMessage,
    MessageType,
    Option,
    Reply,
)
from tee_concierge.domain.ports import CatalogRepository, ConversationRepository, UsageRepository

log = structlog.get_logger()

SESSION_TIMEOUT = timedelta(hours=2)
FAILURES_BEFORE_CONTACT = 2


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MenuEngine:
    """Turns an inbound message into the next menu screen.

    Resolution order: tapped option, typed code, keyword shortcut, then a fallback that
    re-shows the current menu. A new session (first message, or after `SESSION_TIMEOUT`
    of silence) always starts at the main menu.
    """

    def __init__(
        self,
        conversations: ConversationRepository,
        menu: Menu,
        catalog: CatalogRepository,
        usage: UsageRepository,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._conversations = conversations
        self._menu = menu
        self._catalog = catalog
        self._usage = usage
        self._clock = clock

    async def reply_to(self, message: InboundMessage) -> Reply:
        now = self._clock()
        state = await self._conversations.get(message.phone)
        new_session = (
            state is None or state.updated_at is None or now - state.updated_at > SESSION_TIMEOUT
        )
        if state is None or new_session:
            state = ConversationState(phone=message.phone)

        try:
            node_id, failures, reply = await self._resolve(message, state, new_session)
        except (ValueError, KeyError, TypeError):
            # A screen failed to render (e.g. content that breaks WhatsApp limits). Don't leave
            # the customer without an answer. Infrastructure errors still propagate and retry.
            log.exception("render_failed", wamid=message.wamid, node=state.node)
            node_id, failures = MAIN, 0
            reply = Reply(self._menu.messages.error_generic, self._escape_options())
        await self._record_visit(node_id)
        await self._conversations.save(
            ConversationState(message.phone, node=node_id, failures=failures, updated_at=now)
        )
        return reply

    def _escape_options(self) -> tuple[Option, ...]:
        m, contact = self._menu.messages, self._menu.nav.contact
        options = [Option(encode(MAIN), m.label_main)]
        if contact:
            options.append(Option(encode(contact), m.label_contact))
        return tuple(options)

    async def _record_visit(self, node_id: str) -> None:
        try:
            await self._usage.record_visit(node_id)
        except Exception:  # reporting must never break a conversation
            log.warning("usage_not_recorded", node=node_id, exc_info=True)

    async def _resolve(
        self, message: InboundMessage, state: ConversationState, new_session: bool
    ) -> tuple[str, int, Reply]:
        registry = self._menu.registry
        if message.reply_id:
            route = decode(message.reply_id)
            if route and registry.get(route.node):
                return route.node, 0, await self._render(route.node, message, route.args)
            log.info("stale_option_id", option_id=message.reply_id)
            return MAIN, 0, await self._render(MAIN, message)

        if new_session:
            return MAIN, 0, await self._render(MAIN, message)

        text = message.text if message.type is MessageType.TEXT else None
        if text is None:
            return await self._fallback(
                message, state, self._menu.messages.unsupported, count_failure=False
            )

        # A typed code beats keywords: "1.2" or "ENVIOS" jump straight to that node.
        node = registry.by_code(text) or registry.match_keyword(text)
        if node is not None:
            return node.id, 0, await self._render(node.id, message)
        return await self._fallback(
            message, state, self._menu.messages.not_understood, count_failure=True
        )

    async def _fallback(
        self, message: InboundMessage, state: ConversationState, prefix: str, *, count_failure: bool
    ) -> tuple[str, int, Reply]:
        failures = state.failures + (1 if count_failure else 0)
        if failures >= FAILURES_BEFORE_CONTACT:
            reply = Reply(self._menu.messages.not_understood_twice, self._contact_first_options())
            return state.node, failures, reply
        current = await self._render(state.node, message)
        body = f"{prefix}\n\n{current.body}"
        return state.node, failures, Reply(body[:1024], current.options, current.list_button)

    def _contact_first_options(self) -> tuple[Option, ...]:
        m, contact = self._menu.messages, self._menu.nav.contact
        options = [Option(encode(contact), m.label_contact)] if contact else []
        return (*options, Option(encode(MAIN), m.label_main))

    async def _render(
        self, node_id: str, message: InboundMessage, args: tuple[str, ...] = ()
    ) -> Reply:
        node = self._menu.registry.get(node_id) or self._menu.registry.get(MAIN)
        if node is None:
            raise KeyError(MAIN)
        ctx = NodeContext(
            business=self._menu.business,
            catalog=self._catalog,
            messages=self._menu.messages,
            nav=self._menu.nav,
            args=args,
            profile_name=message.profile_name,
        )
        return await node.handler(ctx)
