# tee-concierge

A WhatsApp assistant for a T-shirt store, in Spanish. It greets customers with an interactive menu and guides them through catalog, sizes, prices, stock, shipping, payment and returns using tappable options, and shows how to contact the store when a person is needed.

> **Status:** Phases 1 (foundation), 2 (messaging core) and 3 (conversation engine) done. Phase 4 (catalog and FAQ) is next. See [docs/](docs/).

## Quick start

```bash
cp .env.example .env
make install   # uv sync
make check     # ruff, mypy, import-linter, pytest
make run       # API on http://localhost:8000/health
make up        # full stack with Docker (api, worker, postgres, redis)
make chat      # talk to the bot in your terminal; type a number to tap an option
```

## Why this project exists

A portfolio project meant to show production-minded backend engineering in Python:

- Clean / hexagonal architecture with a clear domain core
- Webhook handling done correctly (signature verification, idempotency, retries)
- A declarative, menu-driven conversation engine (state machine over WhatsApp buttons and lists)
- Observability, testing strategy, CI/CD and containerized deployment
- Decisions recorded as ADRs

## Documentation map

| # | Document | Purpose |
|---|----------|---------|
| 1 | [Product requirements](docs/01-product-requirements.md) | Problem, personas, scope, functional and non-functional requirements |
| 2 | [Architecture](docs/02-architecture.md) | System context, components, layering, data flow, deployment |
| 3 | [Domain model](docs/03-domain-model.md) | Entities, aggregates, ports, database sketch |
| 4 | [Conversation design](docs/04-conversation-design.md) | Menu tree, state machine, WhatsApp limits, contact us |
| 5 | [Tech stack](docs/05-tech-stack.md) | Chosen tools with alternatives considered |
| 6 | [Roadmap](docs/06-roadmap.md) | Phased delivery plan with acceptance criteria |
| 7 | [Risks and open questions](docs/07-risks-and-open-questions.md) | Things to decide or validate before coding |
| 8 | [Meta WhatsApp setup](docs/08-meta-whatsapp-setup.md) | Step-by-step Cloud API account, token and webhook setup |
| - | [ADRs](docs/adr/) | Architecture Decision Records |

## Planned repository layout

```
tee-concierge/
├── docs/                  # You are here
├── src/tee_concierge/
│   ├── domain/            # Entities, value objects, ports (pure Python)
│   ├── application/       # Use cases, conversation engine
│   ├── infrastructure/    # WhatsApp client, DB, cache adapters
│   └── interfaces/        # FastAPI webhook + admin API
├── tests/{unit,integration,e2e}/
├── migrations/
├── docker/
└── pyproject.toml
```
