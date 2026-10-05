# 6. Roadmap

Each phase ends with something demoable, and every phase keeps CI green.

## Phase 0: Analysis and design (done)
- Docs, ADRs and scope. Decisions: Spanish only, menu-driven, no LLM, no orders or payments in the MVP.

## Phase 1: Foundation
- Repo scaffold: `pyproject.toml`, uv, ruff, mypy, pre-commit, import-linter, Makefile
- Docker compose (api, worker, postgres, redis)
- Config, structured logging, health endpoint
- GitHub Actions pipeline
- **Done when** `make up && make test` works from a clean clone.

## Phase 2: Messaging core
- Webhook verification and signature check
- Inbound parsing, persistence with unique `wamid`, enqueue, worker with per-conversation lock
- WhatsApp outbound adapter (text, buttons, list) and a **fake gateway with a CLI chat**
- Echo bot end to end
- **Done when** a duplicated webhook is processed once (integration test) and the bot can reply through the real test number.

## Phase 3: Conversation engine (done)
- Declarative menu node registry, state machine, button-id routing
- Renderers that respect WhatsApp limits (3 buttons, 10 rows, pagination, char limits)
- Main menu, navigation (Volver, Menú principal), keyword shortcuts, fallback
- Spanish copy kept in one content module
- **Done when** "Hola" opens the menu and the whole static tree is navigable, with the path-coverage test passing.

## Phase 4: Catalog and FAQ (done)
- Domain model, migrations, synthetic seed script (categories, products, sizes, colors, stock)
- Catalog browsing nodes: category, product, detail, size and color availability, photos
- FAQ nodes: sizes, shipping, payment, returns, hours and location, from editable content
- **Done when** a customer can go from "Hola" to a product's stock for a size and color, using taps only.

## Phase 5: Contact and message tracking (done)
- "Contáctanos" node and keyword shortcuts (number, `wa.me` link, hours from config)
- Message status tracking (accepted, sent, delivered, read, failed; never moves backwards), inbound messages marked as read, conversation history query
- **Done when** every menu leaf can reach "Contáctanos" and statuses are stored.

## Phase 6: Admin and observability (done, tracing deferred)
- Admin API (catalog, FAQ content, conversations), auth
- Metrics, tracing, menu usage reports
- Rate limits and security review
- **Done when** the owner can change a product or FAQ answer without touching code.

## Phase 7: Showcase and stretch
- Public demo deployment, GIF or video, polished README and diagrams, "lessons learned"
- **Stretch options (pick any):** order status lookup, cart and payment link, optional LLM fallback node, template notifications.
- **Done when** a recruiter can understand the project in 5 minutes and try it in 1 command.
