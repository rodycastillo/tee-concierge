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
- Receive and reply to WhatsApp text messages
- Catalog browsing: list products, filter by size, color, price
- Product details: price, sizes, colors, stock, material, images
- FAQ: shipping, returns, payment methods, store hours, location
- Order status lookup by order number
- Human handoff (keyword or low confidence) with owner notification
- Conversation and message persistence
- Language detection (ES/EN)

### Next (should have)
- Cart and order creation inside chat
- Payment link generation (Stripe or Mercado Pago, to be decided)
- Interactive messages (buttons, lists) and product images
- Admin API and basic dashboard
- Proactive templates (order shipped, cart reminder), opt-in only

### Later (could have)
- Voice note transcription
- Product recommendations from purchase history
- Multi-tenant support
- Analytics dashboard

## 1.5 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Verify the Meta webhook handshake and every `X-Hub-Signature-256` | MUST |
| FR-02 | Process each inbound message exactly once, even if Meta retries | MUST |
| FR-03 | Answer product, price, size and stock questions from the database, never from model memory | MUST |
| FR-04 | Answer FAQ from a curated knowledge base | MUST |
| FR-05 | Detect handoff intent and pause the bot for that conversation | MUST |
| FR-06 | Notify the owner on handoff (WhatsApp message to the owner, or email) | MUST |
| FR-07 | Look up order status, only for the phone number that placed the order | MUST |
| FR-08 | Persist all messages with timestamps and delivery status | MUST |
| FR-09 | Build a cart and create an order through a guided flow | SHOULD |
| FR-10 | Send a payment link and confirm payment via payment webhook | SHOULD |
| FR-11 | Respect the 24h customer-service window; use approved templates outside it | SHOULD |
| FR-12 | Honor STOP / opt-out for proactive messages | MUST (if proactive messages ship) |
| FR-13 | Owner can resume the bot after a handoff | SHOULD |

## 1.6 Non-functional requirements

| Area | Target |
|---|---|
| Latency | Webhook ACK < 1s (ack first, process async); reply p95 < 5s with LLM, < 1.5s rule-based |
| Reliability | No lost messages: persisted before processing, retry with backoff, dead-letter queue |
| Security | Secrets in env/secret manager, signature verification, PII minimization, rate limiting per phone |
| Privacy | Store only what is needed, retention policy, a delete-my-data path (GDPR/LGPD-style) |
| Observability | Structured JSON logs with correlation id, metrics, tracing on the message pipeline |
| Cost | Cap LLM spend per conversation and per day; rules first, LLM only when needed |
| Maintainability | Layered architecture, 85%+ coverage on domain and application, typed (mypy strict) |
| Portability | `docker compose up` runs everything locally with a fake WhatsApp gateway |

## 1.7 Success metrics

- Containment rate: % of conversations resolved without a human
- Correctness: % of answers matching catalog truth (evaluation set)
- Handoff precision: handoffs that were actually needed
- Conversion: conversations that reached an order or payment link
