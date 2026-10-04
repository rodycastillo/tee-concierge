# 7. Risks and Open Questions

## 7.1 Open questions (need your answers before Phase 1)

| # | Question | Why it matters |
|---|---|---|
| Q1 | **Languages:** Spanish only, or Spanish and English? | Prompts, FAQ content, evaluation set |
| Q2 | **Is the store real?** Do you have a real catalog (and where does it live: Shopify, Excel, nothing)? | Decides whether we integrate an existing source or own the catalog DB |
| Q3 | **Meta setup:** do you already have a Meta Business account and a WhatsApp test number? | The sandbox number is enough for dev; production needs business verification |
| Q4 | **Scope of the MVP:** answers only, or also taking orders and payments? | Phase 6 is big |
| Q5 | **Payments:** which provider and country (Stripe, Mercado Pago, others)? | Adapter choice, currency |
| Q6 | **LLM budget:** is there an acceptable monthly cost? | Model routing and caps |
| Q7 | **Hosting:** any preference or free-tier constraint? | Deployment target |
| Q8 | **Repo visibility:** public portfolio repo? | Synthetic demo data only, no real customer data or secrets |
| Q9 | **Owner handoff channel:** the owner's own WhatsApp, email, or a small web inbox? | Notifier adapter |

## 7.2 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| LLM states a wrong price or stock | Lost trust, wrong sales | Tool-only facts, post-check grounding, golden-set tests |
| Meta policy limits (24h window, template approval, business verification delays) | Features blocked | Design around the window early; start verification now |
| Duplicate or out-of-order webhooks | Double replies, corrupted state | Unique `wamid`, per-conversation lock |
| Prompt injection or data leak | Privacy breach | Read-only tools, ownership checks, untrusted-input handling |
| Runaway LLM cost | Bill shock | Per-phone rate limit, daily cap, small-model routing |
| Scope creep | Never finished | Strict phases, each demoable |
| Handling real customer PII in a public repo | Legal | Fake data in repo, secrets in env, retention policy |
| Unofficial WhatsApp libraries | Number ban | Official Cloud API only (see ADR-0001) |

## 7.3 Assumptions

- One store, one WhatsApp number, one owner (multi-tenant is out of scope for v1).
- Meta Cloud API access can be obtained.
- Catalog is small (under 500 variants), so plain SQL search is enough for the MVP.
