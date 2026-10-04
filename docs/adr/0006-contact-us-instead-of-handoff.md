# ADR-0006: "Contáctanos" node instead of live human handoff

- **Status:** Accepted
- **Date:** 2026-10-03

## Context
The initial design had a handoff mode: the bot goes silent and notifies the owner. The product owner prefers that the bot simply gives the customer the store's contact details.

## Decision
Replace handoff with a static **"Contáctanos"** menu node that shows the contact number, a `wa.me` link and opening hours (from configuration). No conversation mode, no owner notifications, no resume logic.

## Consequences
- (+) Much simpler: no extra state, no notifier port, no admin inbox
- (+) The bot never blocks or conflicts with the owner's own chats
- (-) Customers must start a second conversation with the owner; the owner has no context. Can be revisited later with a handoff feature if needed
