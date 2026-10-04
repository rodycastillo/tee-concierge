# ADR-0005: Menu-driven conversation, Spanish only, no LLM in the MVP

- **Status:** Accepted
- **Date:** 2026-10-03
- **Supersedes:** [ADR-0004](0004-hybrid-rules-and-llm.md)

## Context
The product owner decided the bot should always present options (buttons and lists) and customers answer by tapping them. Users write in Spanish. There is no requirement for open-ended natural language.

## Decision
- The conversation engine is a **declarative menu tree plus a state machine**, rendered with WhatsApp interactive messages.
- **No LLM** in the MVP. Free text is handled by keyword matching and a fallback that re-shows the current menu.
- The `LLMClient` port is **not built now**. The architecture leaves room to add an LLM fallback node later.
- Button and row ids encode navigation targets so taps are resolvable without relying on stored state.
- Single language (Spanish), with copy kept in one place so adding a locale later is easy.

## Consequences
- (+) Deterministic, cheap, fast, fully testable; no hallucination risk
- (+) Simpler infrastructure and a smaller scope
- (-) Less flexible with free-form questions; mitigated by keyword shortcuts and human handoff
- (-) Bound by WhatsApp limits (3 buttons, 10 list rows), so the menu needs pagination and careful design
