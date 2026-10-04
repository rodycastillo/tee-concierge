# ADR-0002: Hexagonal architecture with an enforced dependency rule

- **Status:** Accepted
- **Date:** 2026-10-03

## Context
The system integrates four volatile external things (WhatsApp, LLM, payments, database). Business rules (stock, order state, handoff) must stay stable and testable.

## Decision
Four layers: `domain`, `application`, `infrastructure`, `interfaces`. Dependencies point inward. The domain defines ports as `typing.Protocol`. `import-linter` enforces the contracts in CI.

## Consequences
- (+) Domain and use cases are unit-testable with in-memory fakes
- (+) Providers are swappable
- (-) More files and indirection than a simple script; justified by the portfolio goal and the integration count
