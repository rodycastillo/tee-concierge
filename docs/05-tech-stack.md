# 5. Tech Stack

| Layer | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Language | **Python 3.12+** | n/a | Required; mature ecosystem, full typing |
| Web framework | **FastAPI** | Flask, Django | Async, Pydantic validation, OpenAPI for free |
| WhatsApp | **Meta WhatsApp Cloud API** | Twilio, 360dialog, whatsapp-web.js | Official and free tier; a clean adapter keeps Twilio swappable. Unofficial libs risk bans and look bad in a portfolio |
| Database | **PostgreSQL 16** | SQLite, MongoDB | Relational integrity for orders and stock; jsonb for state; pgvector available if FAQ search is needed |
| ORM / migrations | **SQLAlchemy 2.0 (async) + Alembic** | SQLModel, Tortoise | Industry standard, explicit mapping keeps the domain clean |
| Queue / cache | **Redis** with **arq** | Celery, RQ, SQS | Async-native, light. Redis also serves locks and rate limits |
| LLM | **None in the MVP** (see ADR-0005) | Claude, OpenAI | Menu-driven flow needs no model; can be added later behind a port |
| Validation / config | **Pydantic v2, pydantic-settings** | n/a | Typed config, 12-factor |
| HTTP client | **httpx** | aiohttp | Async, easy to mock |
| Logging / metrics | **structlog, prometheus-client, OpenTelemetry** | n/a | Production-grade observability |
| Packaging | **uv** + `pyproject.toml` | Poetry, pip-tools | Fast, lockfile, modern |
| Quality | **ruff, mypy (strict), import-linter, pre-commit** | flake8, black | One fast linter and formatter; layer rules enforced |
| Testing | **pytest, pytest-asyncio, respx, testcontainers, hypothesis** | unittest | Real Postgres and Redis in integration tests |
| Containers | **Docker, docker compose** | n/a | One-command local run |
| CI/CD | **GitHub Actions** | n/a | Visible to recruiters in the repo |

## Tooling for local dev

- `make up`, `make test`, `make lint`, `make seed`, `make chat` (CLI chat against the fake gateway)
- `.env.example` documents every variable
- A devcontainer is optional

## Decision log

Decisions are recorded in [adr/](adr/).
