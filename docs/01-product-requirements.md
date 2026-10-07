# 1. Product Requirements

## 1.1 Problem

A small T-shirt store receives repetitive WhatsApp questions all day ("do you have it in M?", "how much is shipping?", "where is my order?"). The owner answers manually, loses sales after hours, and has no record of what customers ask.

## 1.2 Goals

1. Answer common questions instantly, 24/7, from real catalog and stock data.
2. Convert conversations into orders (or at least into qualified leads).
3. Hand off to the owner when the bot is unsure, or when the customer asks.
4. Give the owner visibility: conversations, unanswered questions, top products.

**Non-goal (as a project):** it is not a general chatbot platform. It is one store, done well, with seams that make multi-tenant a later option.

## 1.3 Personas

| Persona | Needs |
|---|---|
| **Customer** | Fast, accurate answers in their language (ES/EN) inside WhatsApp, no app to install |
| **Store owner** | Control over catalog and policies, takeover of any chat, simple reports |
| **Recruiter / dev reviewing the repo** | Clear README, architecture, tests, one-command local run, demo mode |

## 1.4 Scope

### MVP (must have)
- Spanish only
- **Menu-driven chat:** every bot message offers tappable options (buttons / lists) that fit the context; "Hola" opens the main menu
- Catalog browsing: categories, products, sizes, colors, price, stock, photo
- FAQ nodes: size guide, shipping, payment methods, returns, hours and location
- Graceful handling of free text and unsupported message types (re-show the current menu)
- **"Contáctanos" option:** shows the store's contact number and a click-to-chat link; no handoff mode, the customer talks to the owner on the store's own channel
- Conversation and message persistence
- Demo catalog (synthetic seed data; the real catalog is not available yet)

### Next (should have)
- Order status lookup by order number (needs an order data source)
- Admin API and basic dashboard to manage catalog and FAQ content
- Basic reports: top products, most used menu options, "Contáctanos" taps

### Later (could have)
- Cart, order creation and payment link inside chat
- Proactive templates (order shipped), opt-in only
- Optional LLM fallback for free-text questions
- Voice note transcription, multi-tenant support

**Out of scope for the MVP:** taking orders, payments, LLM answers.

## 1.5 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Verify the Meta webhook handshake and every `X-Hub-Signature-256` | MUST |
| FR-02 | Process each inbound message exactly once, even if Meta retries | MUST |
| FR-03 | Reply to any first message (e.g. "Hola") with the main menu | MUST |
| FR-04 | Every bot reply includes options valid for the current context, and navigation (Volver, Menú principal) | MUST |
| FR-05 | Resolve a tapped option from its id alone, even if stored state is stale | MUST |
| FR-06 | Product, price, size and stock data come from the database | MUST |
| FR-07 | Menu and answers come from a business's config file (ADR-0007), not hard-coded strings | MUST |
| FR-08 | Free text: keyword shortcuts, otherwise "no entendí" and the current menu again | MUST |
| FR-09 | "Contáctanos" node shows the store's contact number / `wa.me` link (configurable) and the opening hours | MUST |
| FR-10 | Persist all messages with timestamps and delivery status | MUST |
| FR-11 | Respect WhatsApp list/button limits (3 buttons, 10 rows) with pagination | MUST |
| FR-12 | Order status lookup, only for the phone number that placed the order | SHOULD |

## 1.6 Non-functional requirements

| Area | Target |
|---|---|
| Latency | Webhook ACK < 1s (ack first, process async); reply p95 < 1.5s |
| Reliability | No lost messages: persisted before processing, retry with backoff, dead-letter queue |
| Security | Secrets in env/secret manager, signature verification, PII minimization, rate limiting per phone |
| Privacy | Store only what is needed, retention policy, a delete-my-data path (GDPR/LGPD-style) |
| Observability | Structured JSON logs with correlation id, metrics, tracing on the message pipeline |
| Cost | Runs on free tiers; no per-message AI cost |
| Maintainability | Layered architecture, 85%+ coverage on domain and application, typed (mypy strict) |
| Portability | `docker compose up` runs everything locally with a fake WhatsApp gateway |

## 1.7 Success metrics

- Containment rate: % of conversations resolved without a human
- Dead-end rate: % of sessions ending on a "no entendí" loop (should trend to 0)
- Menu usage: most visited nodes, to improve the tree
- "Contáctanos" taps and the places they happen from
