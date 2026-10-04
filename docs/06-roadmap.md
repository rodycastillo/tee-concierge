# 6. Roadmap

Each phase ends with something demoable, and every phase keeps CI green.

## Phase 0: Analysis and design (current)
- Docs, ADRs, scope. **Done when** the open questions in doc 07 are answered.

## Phase 1: Foundation
- Repo scaffold: `pyproject.toml`, uv, ruff, mypy, pre-commit, import-linter, Makefile
- Docker compose (api, worker, postgres, redis)
- Config, structured logging, health endpoint
- GitHub Actions pipeline
- **Done when** `make up && make test` works from a clean clone.

## Phase 2: Messaging core
- Webhook verification and signature check
- Inbound parsing, persistence with unique `wamid`, enqueue, worker
- WhatsApp outbound adapter and **fake gateway + CLI chat**
- Echo bot end to end
- **Done when** a duplicated webhook is processed once (integration test) and the bot can echo through the real test number.

## Phase 3: Catalog and FAQ
- Domain model, migrations, seed script
- Use cases: search products, product detail, stock
- Rule-based router and FAQ answers, ES/EN
- Buttons and list messages
- **Done when** the customer can browse and ask about size, price and stock with no LLM.

## Phase 4: LLM agent
- `LLMClient` port and Claude adapter, tool registry, grounding checks
- Conversation memory and summarization, cost caps, fallback
- Golden-set evaluation in CI
- **Done when** free-text questions work and the evaluation set passes its thresholds.

## Phase 5: Handoff and order status
- Handoff mode, owner notification, resume
- Order status lookup with phone ownership check
- **Done when** the bot goes silent in HUMAN mode and resumes on command.

## Phase 6: Checkout and payments
- Cart, address collection, order creation, payment link, payment webhook with idempotency
- **Done when** the full purchase flow works in the sandbox.

## Phase 7: Hardening and showcase
- Admin API, metrics dashboard (Grafana), tracing
- Load test, security review, rate limits
- Deploy a public demo, record a GIF or video, finalize the README, architecture diagrams and a "lessons learned" section
- **Done when** a recruiter can understand the project in 5 minutes and try it in 1 command.
