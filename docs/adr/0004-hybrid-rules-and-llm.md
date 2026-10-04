# ADR-0004: Hybrid conversation engine (rules and state machine, then LLM with tools)

- **Status:** Superseded by [ADR-0005](0005-menu-driven-conversation.md)
- **Date:** 2026-10-03

## Context
A pure-LLM bot is flexible but can hallucinate prices and costs money per message. A pure-rules bot is reliable but rigid.

## Decision
Order of processing: rules, then active flow (state machine), then LLM agent with read-only tools, then fallback or handoff. Facts (price, stock, order status) come only from tool results. Checkout is always a deterministic flow.

## Consequences
- (+) Cheaper, faster for common messages; grounded answers; auditable checkout
- (+) The LLM is replaceable behind the `LLMClient` port
- (-) Two systems to maintain and a routing layer to test; mitigated by a golden evaluation set
