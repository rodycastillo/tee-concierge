# ADR-0003: Acknowledge webhooks immediately, process asynchronously

- **Status:** Accepted
- **Date:** 2026-10-03

## Context
Meta expects a fast 200 response and retries otherwise. Our processing involves database reads and LLM calls that can take several seconds. Retries cause duplicates.

## Decision
The webhook endpoint only: (1) verifies the HMAC signature, (2) inserts the inbound message with a unique `wamid`, (3) enqueues a job, (4) returns 200. A worker consumes jobs, takes a per-conversation lock and runs the conversation engine.

## Consequences
- (+) Fast ACK, no duplicate processing, messages are persisted before any failure can occur
- (+) The worker scales independently and supports retries and a DLQ
- (-) Adds Redis and a worker process to operate
- (-) Needs the per-conversation lock to keep message order
