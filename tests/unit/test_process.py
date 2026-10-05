from tee_concierge.application.process import ProcessInboundMessage
from tee_concierge.domain.messaging import InboundMessage, Reply
from tee_concierge.infrastructure.whatsapp.parser import parse_inbound_messages
from tee_concierge.infrastructure.whatsapp.simulator import text_payload
from tests.fakes import InMemoryMessageRepository, NoopLock, RecordingGateway


class StubResponder:
    async def reply_to(self, message: InboundMessage) -> Reply:
        return Reply(f"eco: {message.text}")


async def _setup() -> tuple[InMemoryMessageRepository, RecordingGateway, ProcessInboundMessage]:
    repo, gateway = InMemoryMessageRepository(), RecordingGateway()
    for msg in parse_inbound_messages(text_payload("51911111111", "Hola", "wamid.1")):
        await repo.add_inbound(msg)
    return repo, gateway, ProcessInboundMessage(repo, gateway, NoopLock(), StubResponder())


async def test_replies_persists_outbound_and_marks_processed() -> None:
    repo, gateway, process = await _setup()

    await process.execute("wamid.1")

    assert gateway.sent == [("51911111111", Reply("eco: Hola"))]
    assert repo.outbound == [("51911111111", Reply("eco: Hola"), "out.1")]
    assert "wamid.1" in repo.processed


async def test_running_the_job_twice_replies_once() -> None:
    _, gateway, process = await _setup()

    await process.execute("wamid.1")
    await process.execute("wamid.1")

    assert len(gateway.sent) == 1


async def test_unknown_message_is_skipped() -> None:
    _, gateway, process = await _setup()
    await process.execute("does-not-exist")
    assert gateway.sent == []


async def test_inbound_message_is_marked_read_before_replying() -> None:
    _, gateway, process = await _setup()

    await process.execute("wamid.1")

    assert gateway.read == ["wamid.1"]


async def test_a_failing_mark_read_does_not_block_the_reply() -> None:
    _, gateway, process = await _setup()
    gateway.fail_mark_read = True

    await process.execute("wamid.1")

    assert len(gateway.sent) == 1
