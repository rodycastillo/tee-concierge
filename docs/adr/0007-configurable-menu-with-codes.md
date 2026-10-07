# ADR-0007: Configurable menu with codes, for any business

- **Status:** Accepted
- **Date:** 2026-10-06
- **Extends:** [ADR-0005](0005-menu-driven-conversation.md)

## Context
The bot was built for one T-shirt store: the menu tree, the Spanish copy and the catalog screens were all in code. The goal changed: it should serve **any business** (a clinic, a restaurant, a shop) without programming, through a menu whose options have **codes**.

## Decision
- The menu is **data**, not code: a YAML file describes the business and a tree of nodes. The engine builds its node registry from it at startup.
- Each node has a **code** (explicit, or auto-numbered by position: `1`, `1.2`, ...). A customer can **tap** an option or **type its code** from any screen; codes are global and matched before keywords. `0` always returns to the main menu. Codes are shown in the option titles (configurable).
- Node **types**: `menu` (children), `text`, `contact`, and `catalog` (the existing data-driven catalog, optional and at most one). More types can be added by registering a builder.
- **One business per deployment** (no multi-tenancy). The file is chosen with `MENU_CONFIG`; `examples/` ships two businesses (T-shirt store, dental clinic) to prove it is generic.
- All customer-facing strings are a `Messages` object with Spanish defaults that the config can override, so another language needs no code change.
- The config is **validated before it can break a customer**: schema (Pydantic), structural rules (unique ids and codes, WhatsApp limits on children) and a dry-run render of every reachable screen. `tee-menu validate` runs the same checks in CI.
- The editable-FAQ table is removed: FAQ answers are now `text` nodes in the file (versioned and reviewable).

## Consequences
- (+) A new business is a new YAML file; no code or deploy of new logic
- (+) Misconfiguration is caught at startup and in CI, not by a customer
- (+) Codes also give a typed shortcut that works on any WhatsApp client
- (-) Editing the menu means editing a file and restarting; a runtime editor (admin API import) is a later step
- (-) A single shared `Messages` set means per-node localization is out of scope
- Contact numbers and hours are overridable from the environment, so real data never has to be committed
