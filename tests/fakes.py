from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from tee_concierge.domain.messaging import InboundMessage, StoredReply


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self.inbound: dict[str, InboundMessage] = {}
        self.processed: set[str] = set()
        self.outbound: list[tuple[str, str, str | None]] = []

    async def add_inbound(self, message: InboundMessage) -> bool:
        if message.wamid in self.inbound:
            return False
        self.inbound[message.wamid] = message
        return True

    async def get_unprocessed(self, wamid: str) -> InboundMessage | None:
        if wamid in self.processed:
            return None
        return self.inbound.get(wamid)

    async def mark_processed(self, wamid: str) -> None:
        self.processed.add(wamid)

    async def add_outbound(self, phone: str, body: str, wamid: str | None) -> None:
        self.outbound.append((phone, body, wamid))

    async def list_outbound(self, phone: str, after_id: int = 0) -> list[StoredReply]:
        return []


class RecordingQueue:
    def __init__(self, fail_times: int = 0) -> None:
        self.jobs: list[str] = []
        self._fail_times = fail_times

    async def enqueue_inbound(self, wamid: str) -> None:
        if self._fail_times:
            self._fail_times -= 1
            raise ConnectionError("redis down")
        self.jobs.append(wamid)


class RecordingGateway:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_text(self, to: str, body: str) -> str | None:
        self.sent.append((to, body))
        return f"out.{len(self.sent)}"


class NoopLock:
    @asynccontextmanager
    async def hold(self, key: str) -> AsyncIterator[None]:
        yield
