from fastapi import Request

from tee_concierge.application.ingest import IngestWebhook
from tee_concierge.domain.ports import MessageRepository


def get_ingest(request: Request) -> IngestWebhook:
    ingest: IngestWebhook = request.app.state.ingest
    return ingest


def get_repository(request: Request) -> MessageRepository:
    repo: MessageRepository = request.app.state.repo
    return repo
