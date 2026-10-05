import json
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tee_concierge.application.ingest import IngestWebhook
from tee_concierge.config import Settings, get_settings
from tee_concierge.infrastructure.whatsapp.parser import parse_webhook
from tee_concierge.infrastructure.whatsapp.signature import sign
from tee_concierge.infrastructure.whatsapp.simulator import text_payload
from tee_concierge.interfaces.api.main import create_app
from tests.fakes import InMemoryMessageRepository, RecordingQueue

SECRET = "test-secret"


@asynccontextmanager
async def _no_lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def queue() -> RecordingQueue:
    return RecordingQueue()


@pytest.fixture
def client(queue: RecordingQueue) -> Iterator[TestClient]:
    app = create_app(lifespan=_no_lifespan)
    repo = InMemoryMessageRepository()
    app.state.repo = repo
    app.state.ingest = IngestWebhook(repo, queue, parse_webhook)
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, whatsapp_app_secret=SECRET, whatsapp_verify_token="verify-me"
    )
    with TestClient(app) as test_client:
        yield test_client


def _post(client: TestClient, payload: dict, signature: str | None = None):  # type: ignore[no-untyped-def,type-arg]
    body = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": signature or sign(SECRET, body)}
    return client.post("/webhook", content=body, headers=headers)


def test_handshake_returns_challenge_for_the_right_token(client: TestClient) -> None:
    params = {"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "1234"}
    response = client.get("/webhook", params=params)
    assert (response.status_code, response.text) == (200, "1234")


def test_handshake_rejects_the_wrong_token(client: TestClient) -> None:
    params = {"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "1"}
    assert client.get("/webhook", params=params).status_code == 403


def test_bad_signature_is_rejected_and_nothing_is_enqueued(
    client: TestClient, queue: RecordingQueue
) -> None:
    response = _post(client, text_payload("51911111111", "Hola", "w1"), signature="sha256=bad")
    assert response.status_code == 401
    assert queue.jobs == []


def test_signed_message_is_accepted_and_a_redelivery_is_not_stored_again(
    client: TestClient, queue: RecordingQueue
) -> None:
    payload = text_payload("51911111111", "Hola", "w1")

    first = _post(client, payload)
    second = _post(client, payload)

    assert first.json() == {"status": "ok", "accepted": 1}
    assert second.json() == {"status": "ok", "accepted": 0}
    # The redelivery re-enqueues the still-unprocessed message; arq dedupes by job id.
    assert set(queue.jobs) == {"w1"}
