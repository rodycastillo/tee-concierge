import pytest

from tee_concierge.application.ingest import IngestWebhook
from tee_concierge.infrastructure.whatsapp.parser import parse_inbound_messages
from tee_concierge.infrastructure.whatsapp.simulator import text_payload
from tests.fakes import InMemoryMessageRepository, RecordingQueue


def _ingest(repo: InMemoryMessageRepository, queue: RecordingQueue) -> IngestWebhook:
    return IngestWebhook(repo, queue, parse_inbound_messages)


async def test_new_message_is_stored_and_enqueued_once() -> None:
    repo, queue = InMemoryMessageRepository(), RecordingQueue()
    payload = text_payload("51911111111", "Hola", "wamid.1")

    assert await _ingest(repo, queue).execute(payload) == 1
    assert queue.jobs == ["wamid.1"]


async def test_duplicate_delivery_after_processing_is_ignored() -> None:
    repo, queue = InMemoryMessageRepository(), RecordingQueue()
    ingest = _ingest(repo, queue)
    payload = text_payload("51911111111", "Hola", "wamid.1")
    await ingest.execute(payload)
    await repo.mark_processed("wamid.1")

    assert await ingest.execute(payload) == 0
    assert queue.jobs == ["wamid.1"]


async def test_retry_re_enqueues_a_message_stored_but_never_enqueued() -> None:
    repo, queue = InMemoryMessageRepository(), RecordingQueue(fail_times=1)
    ingest = _ingest(repo, queue)
    payload = text_payload("51911111111", "Hola", "wamid.1")

    with pytest.raises(ConnectionError):
        await ingest.execute(payload)  # stored, enqueue failed -> Meta will retry
    assert await ingest.execute(payload) == 0

    assert queue.jobs == ["wamid.1"]
