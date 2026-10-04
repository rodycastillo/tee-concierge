import itertools

import structlog

log = structlog.get_logger()


class FakeGateway:
    """Local gateway: sends nothing. The reply is stored by the application and
    read back through the dev outbox endpoint (see `tee-chat`)."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)

    async def send_text(self, to: str, body: str) -> str | None:
        wamid = f"fake.out.{next(self._counter)}"
        log.info("fake_send", to=to, body=body, wamid=wamid)
        return wamid
