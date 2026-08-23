---
name: finance-control-api
description: Use this skill whenever the user wants to implement any feature, page, component, hook, or service that touches the financial-api. This includes: listing or managing transactions (create, edit, delete, bulk upload), bank accounts (create, update, delete), browsing available banks, viewing credit installments, checking account balances, and managing fixed/recurring expenses. Trigger even when the request is phrased loosely — "add a spend", "show my balance", "recurring bills page", "upload my statement" all apply. This skill provides API contracts, coding standards, and implementation patterns — always consult it before writing any code related to financial data.
---

# Setup
Finance Control API — Implementation Skill
You are a senior engineer writing production-grade code. Every implementation must meet
the bar of a high-quality tech company: type-safe, secure, performant, testable, and readable.
No shortcuts. No any. No unhandled promises.

References
Load these files on demand — do not load all upfront:

- references/endpoints.md — full endpoint contracts, required fields, request/response shapes.
Read this before implementing any API call.
- references/api-overview.md — base URL, auth header, pagination rules, status codes.
Read this if you need general API behavior or error handling rules.
- For complex details -> read: references/financial_control.json

# Monetary values
value, start_value, current_balance, etc. are returned as decimal strings. There is a function in src/lib/utils to parse the values. use it.

# Implementation checklist
Before marking any task done, verify:

 API call goes through the central client, not raw fetch
 Service function is typed — no any, no untyped responses
 All three UI states handled: loading (skeleton), error (message), success (data)
 Forms validate with zod before submitting
 422 field errors surfaced to the correct input
 Monetary values formatted through formatMoney, never inline
 Mutations invalidate the relevant query cache on success
 No sensitive data (tokens, raw error bodies) exposed to the UI


