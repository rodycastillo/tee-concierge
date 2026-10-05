import uuid

import structlog

from tee_concierge.domain.messaging import Reply

log = structlog.get_logger()


class FakeGateway:
    """Local gateway: sends nothing. The reply is stored by the application and
    read back through the dev outbox endpoint (see `tee-chat`)."""

    async def mark_read(self, wamid: str) -> None:
        log.info("fake_mark_read", wamid=wamid)

    async def send(self, to: str, reply: Reply) -> str | None:
        # uuid, not a counter: ids must stay unique across restarts (wamid is unique in the DB)
        wamid = f"fake.out.{uuid.uuid4().hex}"
        log.info("fake_send", to=to, kind=reply.kind.value, body=reply.body, wamid=wamid)
        return wamid
