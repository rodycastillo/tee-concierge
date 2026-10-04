from tee_concierge.application.process import EchoResponder, ProcessInboundMessage
from tee_concierge.infrastructure.whatsapp.parser import parse_inbound_messages
from tee_concierge.infrastructure.whatsapp.simulator import text_payload
from tests.fakes import InMemoryMessageRepository, NoopLock, RecordingGateway


async def _setup() -> tuple[InMemoryMessageRepository, RecordingGateway, ProcessInboundMessage]:
    repo, gateway = InMemoryMessageRepository(), RecordingGateway()
    for msg in parse_inbound_messages(text_payload("51911111111", "Hola", "wamid.1")):
        await repo.add_inbound(msg)
    return repo, gateway, ProcessInboundMessage(repo, gateway, NoopLock(), EchoResponder())


async def test_replies_persists_outbound_and_marks_processed() -> None:
    repo, gateway, process = await _setup()

    await process.execute("wamid.1")

    assert gateway.sent == [("51911111111", "Recibido: Hola")]
    assert repo.outbound == [("51911111111", "Recibido: Hola", "out.1")]
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
