---
name: HITL trigger flake fires in setup, upstream of every assertion
description: A dead turn in _reach_sensitive_action_card is never a sanctioned-RED member — re-run it; wall clock is not a tell, allure is the only evidence
type: project
aliases: [trigger flake, chat-answer-thought-accordion, sensitive action card never appears, HITL setup]
tags: [area/chat-hitl, type/flake]
created: 2026-08-27
updated: 2026-08-27
---

## Shape

`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`'s shared
`_reach_sensitive_action_card` occasionally dies because the LLM never starts a
turn. Two observed symptoms, same cause:

- Step 2 — `chat-answer-thought-accordion` never visible (60 s exhausted).
  ELITEA-2213, 1 of 4 runs, 2026-08-27.
- Step 3 — `Sensitive Action Authorization card should appear`. ELITEA-2212,
  1 of 6 runs.

It is a **raw uncaught assertion upstream of everything either case asserts**,
so it is never a member of a closed sanctioned-RED set and blocks the gate by
construction. **Re-run it.**

## Two things that cost time when triaging it

- **Wall clock is not a tell.** The ELITEA-2212 occurrence was short (52 s vs
  ~125 s); the ELITEA-2213 one was *long* (450 s — slow fixtures plus the full
  60 s accordion wait). Both directions.
- **The pytest tail may not carry it.** Read
  `reports/allure-results/*-result.json` and match on `fullName`; that is where
  the message and call log survive.

Guardrails hygiene (#1838) held across all 4 runs: `sensitive_tools` was `{}`
before and after every one.

Related: [[soft_absence_assertion_races_the_reappearance]]
