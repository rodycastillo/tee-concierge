from arq.connections import ArqRedis


class ArqJobQueue:
    """Enqueues `process_inbound` jobs. The wamid is the job id, so arq refuses
    duplicates while the job (or its kept result) exists."""

    def __init__(self, pool: ArqRedis) -> None:
        self._pool = pool

    async def enqueue_inbound(self, wamid: str) -> None:
        await self._pool.enqueue_job("process_inbound", wamid, _job_id=wamid)
