# 9. Security and Operations

## 9.1 Threat model (what we defend against)

| Threat | Control | Where |
|---|---|---|
| Forged webhook calls (anyone can POST to a public URL) | HMAC-SHA256 of the raw body with the app secret, compared in constant time; unsigned or wrong requests get 401 and are never stored | `infrastructure/whatsapp/signature.py`, `interfaces/api/webhook.py` |
| Webhook handshake abuse | Verify token compared in constant time | `interfaces/api/webhook.py` |
| Meta retries / replayed deliveries | Unique `wamid` constraint; duplicate ignored; re-enqueue only if still unprocessed | `application/ingest.py` |
| Message flooding / cost abuse | Per-customer fixed-window limit (default 20/min); excess is dropped silently, not answered | `infrastructure/queue/rate_limiter.py` |
| Concurrent messages corrupting a conversation | Per-customer Redis lock around state read-modify-write | `infrastructure/queue/lock.py` |
| Unauthorized admin access | `X-Admin-Key`, constant-time compare; **the API returns 404 (disabled) when no key is configured**, so a missing config can never mean "open" | `interfaces/api/admin.py` |
| Admin input that breaks customer screens (text over WhatsApp's 1024-char limit) | Validated on save; the engine also falls back to a safe reply if a screen still fails to render | `application/admin.py`, `application/engine/engine.py` |
| SSRF / unsafe media | Product images must be `https` URLs; the server never fetches them (WhatsApp does) | `application/admin.py` |
| Secret leakage | `SecretStr` for every secret; `.env` is git-ignored; only `.env.example` is committed with dev-only values | `config.py` |
| PII in logs | Rate-limit log lines carry only the last 4 digits of the phone; message bodies are logged only by the fake gateway | worker, `fake.py` |
| Prompt injection | Not applicable: there is no LLM; user text is only matched against keywords | ADR-0005 |

## 9.2 Known limitations (honest list)

- **At-least-once delivery.** If the worker dies after sending a reply but before recording it, a retry sends the reply again. Fixing it needs an outbox pattern; deliberately left out for a bot whose replies are idempotent menus.
- **A receipt can arrive before its outbound row is stored** (the worker is still writing). It is logged and ignored; the status stays `accepted`.
- **Fixed-window rate limiting** allows a short burst of up to 2x the limit across a window boundary.
- **No tracing yet.** Logs carry the `wamid` as a correlation id; OpenTelemetry spans are not implemented.
- **Admin auth is a single shared key.** Fine for one owner; not for a team. Rotate by changing the env var.
- **Customer data retention.** Messages are kept indefinitely. A delete-my-data endpoint and a retention job are not built.
- **Graph API behaviour** (interactive payloads, mark-as-read) is covered by unit tests only; it has not been exercised against the real Cloud API.

## 9.3 Observability

| Signal | Source | How to read it |
|---|---|---|
| Structured JSON logs | API and worker (`structlog`) | `make logs`; every job line carries `wamid` |
| Webhook outcomes | `tee_webhook_requests_total{outcome}` | API `GET /metrics/` |
| Messages ingested | `tee_messages_ingested_total` | API `/metrics/` |
| Job outcomes and failures | `tee_messages_processed_total{outcome}`, `tee_job_failures_total` | Worker `:9100/metrics` |
| Processing latency | `tee_process_seconds` histogram | Worker `:9100/metrics` |
| Menu usage, message counts | `GET /admin/stats` | Admin API |

Suggested alerts: `tee_job_failures_total` increasing, `tee_webhook_requests_total{outcome="bad_signature"}` spiking (probing), `rate_limited` spiking (abuse).

## 9.4 Operating the admin API

```bash
export KEY=$(grep ADMIN_API_KEY .env | cut -d= -f2)
curl -H "X-Admin-Key: $KEY" localhost:8000/admin/stats
curl -X PATCH -H "X-Admin-Key: $KEY" -H 'content-type: application/json' \
     -d '{"stock": 12}' localhost:8000/admin/variants/5
```

Interactive docs are served at `/docs` (OpenAPI).

## 9.5 Production checklist

- [ ] `WHATSAPP_GATEWAY=cloud` with a permanent system-user token (see doc 8)
- [ ] A strong `WHATSAPP_APP_SECRET`, never the dev value `local-dev-secret`
- [ ] `ADMIN_API_KEY` set (`openssl rand -hex 32`), served only over HTTPS
- [ ] The `/dev/*` routes are mounted only with the fake gateway; confirm they 404 in prod
- [ ] Postgres and Redis not exposed publicly (compose publishes them for local dev only)
- [ ] Real menu file (`MENU_CONFIG`, checked with `tee-menu validate`) and, if it has a catalog, real products (the seed is demo data)
- [ ] Backups for Postgres
