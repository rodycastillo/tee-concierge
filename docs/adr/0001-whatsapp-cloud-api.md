# ADR-0001: Use the official WhatsApp Cloud API behind a gateway port

- **Status:** Accepted
- **Date:** 2026-10-03

## Context
We need to send and receive WhatsApp messages. Options: Meta Cloud API, Twilio, a BSP such as 360dialog, or unofficial libraries that automate WhatsApp Web.

## Decision
Use the **Meta WhatsApp Cloud API**, accessed only through a `MessageGateway` port. Provide a `FakeGateway` for local development and tests.

## Consequences
- (+) Official, stable and free to start; no ban risk
- (+) The port allows moving to Twilio with one new adapter
- (+) The fake gateway lets anyone run the demo with no account
- (-) Requires a Meta Business setup, template approval and the 24h window rules
- Unofficial libraries are rejected: they can get the number banned and violate ToS.
