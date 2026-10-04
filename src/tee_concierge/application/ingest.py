from collections.abc import Callable
from typing import Any

import structlog

from tee_concierge.domain.messaging import InboundMessage
from tee_concierge.domain.ports import JobQueue, MessageRepository

log = structlog.get_logger()

PayloadParser = Callable[[dict[str, Any]], list[InboundMessage]]


class IngestWebhook:
    """Store each inbound message once and schedule its processing.

    Duplicates (Meta retries) are not stored again, but if the earlier attempt
    stored the message and failed to enqueue it, the retry re-enqueues it.
    The queue is idempotent per wamid, so re-enqueueing is safe.
    """

    def __init__(self, repo: MessageRepository, queue: JobQueue, parser: PayloadParser) -> None:
        self._repo = repo
        self._queue = queue
        self._parser = parser

    async def execute(self, payload: dict[str, Any]) -> int:
        """Returns the number of newly stored messages."""
        new = 0
        for message in self._parser(payload):
            if await self._repo.add_inbound(message):
                new += 1
            elif await self._repo.get_unprocessed(message.wamid) is None:
                log.info("duplicate_ignored", wamid=message.wamid)
                continue
            await self._queue.enqueue_inbound(message.wamid)
        return new
