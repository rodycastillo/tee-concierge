from prometheus_client import Counter, Histogram

WEBHOOK_REQUESTS = Counter("tee_webhook_requests_total", "Webhook POSTs by outcome", ["outcome"])
MESSAGES_INGESTED = Counter("tee_messages_ingested_total", "New inbound messages stored")
MESSAGES_PROCESSED = Counter(
    "tee_messages_processed_total", "Jobs finished by outcome", ["outcome"]
)
JOB_FAILURES = Counter("tee_job_failures_total", "process_inbound attempts that raised")
PROCESS_SECONDS = Histogram(
    "tee_process_seconds",
    "Time to process one inbound message",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
