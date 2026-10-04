import hmac
import json
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from tee_concierge.application.ingest import IngestWebhook
from tee_concierge.config import Settings, get_settings
from tee_concierge.infrastructure.whatsapp.signature import verify_signature
from tee_concierge.interfaces.api.dependencies import get_ingest

router = APIRouter(tags=["webhook"])
log = structlog.get_logger()


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    settings: Annotated[Settings, Depends(get_settings)],
    mode: Annotated[str, Query(alias="hub.mode")] = "",
    token: Annotated[str, Query(alias="hub.verify_token")] = "",
    challenge: Annotated[str, Query(alias="hub.challenge")] = "",
) -> str:
    """Meta's subscription handshake."""
    expected = settings.whatsapp_verify_token.get_secret_value()
    if mode != "subscribe" or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="verification failed")
    return challenge


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    ingest: Annotated[IngestWebhook, Depends(get_ingest)],
) -> dict[str, Any]:
    """Verify, store, enqueue, acknowledge. Heavy work happens in the worker."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(settings.whatsapp_app_secret.get_secret_value(), body, signature):
        log.warning("invalid_signature")
        raise HTTPException(status_code=401, detail="invalid signature")
    try:
        payload = json.loads(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    accepted = await ingest.execute(payload)
    return {"status": "ok", "accepted": accepted}
