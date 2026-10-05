# 7. Risks and Open Questions

## 7.1 Decisions made

| # | Question | Answer |
|---|---|---|
| Q1 | Languages | **Spanish only** |
| Q4 | MVP scope | **Chat only, menu-driven, no orders or payments** (see ADR-0005) |
| Q2 | Catalog | **Not available yet**, so we use a synthetic seed catalog. The DB is the source of truth for now |
| Q9 | Human contact | **No handoff.** The bot replies with the store's contact number / link (ADR-0006) |
| Q10 | Store name | **Tee Concierge** (tone of voice and FAQ content still to be written) |
| Q12 | Country and currency | **Peru, PEN (soles)**. Prices shown as `S/ 59.90`; shipping copy for Lima and provinces |
| Q8 | Repo | Already created, so we treat it as a public portfolio repo: synthetic data only, no secrets |

## 7.2 Still open (none block Phase 1)

| # | Question | Needed by |
|---|---|---|
| Q3 | Meta Business account and WhatsApp test number: needed to test against the real Cloud API (the bot is only verified with the fake gateway so far) | Before going live |
| Q7 | Hosting preference or free-tier constraints | Phase 7 |
| Q14 | FAQ answers (sizes, shipping, payment, returns) are generic placeholders seeded into `faq_entries`; replace with the real policies, and replace the demo catalog with real products and photo URLs | Before going live |
| Q13 | The real contact number and opening hours | Phase 5 |
| Q10b | Tone of voice and real FAQ content (shipping zones and costs, return policy, hours, payment methods such as Yape/Plin/transfer) | Phase 4 |
| Q11 | Order status: where would order data come from, given there is no catalog or order system yet? | Stretch |

## 7.3 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Menu too deep or too long for WhatsApp limits (3 buttons, 10 rows) | Poor UX | Declarative tree, pagination, automated limit checks in tests |
| Customers type free text and get stuck | Frustration | Keyword shortcuts, fallback re-shows the menu, offer "Contáctanos" after 2 failures |
| Meta policy limits (24h window, business verification delays) | Features blocked | Bot is reactive only, so it stays in the window; start verification early |
| Duplicate or out-of-order webhooks | Double replies, corrupted state | Unique `wamid`, per-conversation lock |
| Stale interactive messages (customer taps an old menu) | Wrong state | Button ids encode the target node, so routing needs no stored state |
| Public repo with real data | Privacy | Synthetic data only, secrets in env, `.env.example` |
| Scope creep | Never finished | Strict phases, each demoable |
| Unofficial WhatsApp libraries | Number ban | Official Cloud API only (ADR-0001) |

## 7.4 Assumptions

- One store, one WhatsApp number, one owner (multi-tenant is out of scope).
- Catalog is small (under 500 variants), so plain SQL queries are enough.
- Customers use a recent WhatsApp client that renders interactive messages.
