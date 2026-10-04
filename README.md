# tee-concierge

A WhatsApp sales assistant for a T-shirt store. It answers customer questions (catalog, sizes, prices, stock, shipping, order status), guides customers toward a purchase, and hands off to a human when it should.

> **Status:** Phase 0, analysis and design. No code yet. See [docs/](docs/).

## Why this project exists

A portfolio project meant to show production-minded backend engineering in Python:

- Clean / hexagonal architecture with a clear domain core
- Webhook handling done correctly (signature verification, idempotency, retries)
- A hybrid conversation engine: deterministic flows for money-related steps, LLM for natural language
- Observability, testing strategy, CI/CD and containerized deployment
- Decisions recorded as ADRs

## Documentation map

| # | Document | Purpose |
|---|----------|---------|
| 1 | [Product requirements](docs/01-product-requirements.md) | Problem, personas, scope, functional and non-functional requirements |
| 2 | [Architecture](docs/02-architecture.md) | System context, components, layering, data flow, deployment |
| 3 | [Domain model](docs/03-domain-model.md) | Entities, aggregates, ports, database sketch |
| 4 | [Conversation design](docs/04-conversation-design.md) | Intents, state machine, LLM vs rules, handoff, guardrails |
| 5 | [Tech stack](docs/05-tech-stack.md) | Chosen tools with alternatives considered |
| 6 | [Roadmap](docs/06-roadmap.md) | Phased delivery plan with acceptance criteria |
| 7 | [Risks and open questions](docs/07-risks-and-open-questions.md) | Things to decide or validate before coding |
| - | [ADRs](docs/adr/) | Architecture Decision Records |

## Planned repository layout

```
tee-concierge/
├── docs/                  # You are here
├── src/tee_concierge/
│   ├── domain/            # Entities, value objects, ports (pure Python)
│   ├── application/       # Use cases, conversation engine
│   ├── infrastructure/    # WhatsApp client, DB, LLM, cache adapters
│   └── interfaces/        # FastAPI webhook + admin API
├── tests/{unit,integration,e2e}/
├── migrations/
├── docker/
└── pyproject.toml
```
