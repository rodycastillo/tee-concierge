from typing import Annotated

from fastapi import APIRouter, Depends

from tee_concierge.domain.ports import MessageRepository
from tee_concierge.interfaces.api.dependencies import get_repository

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/outbox/{phone}")
async def outbox(
    phone: str,
    repo: Annotated[MessageRepository, Depends(get_repository)],
    after_id: int = 0,
) -> list[dict[str, object]]:
    """Replies the bot produced for `phone`. Only mounted with the fake gateway."""
    replies = await repo.list_outbound(phone, after_id)
    return [{"id": r.id, "body": r.body} for r in replies]
