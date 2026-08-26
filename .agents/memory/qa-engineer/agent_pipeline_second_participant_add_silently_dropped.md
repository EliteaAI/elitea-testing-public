---
name: Second Agent/Pipeline chat participant add is silently dropped
description: Whichever of Agent/Pipeline is added second to a conversation vanishes, both orders, clean console — #1279, not fixed
type: feedback
aliases: [1279, participant silent drop, PIPELINES section missing, four participant types]
tags: [area/chat, type/product-defect]
created: 2026-08-27
updated: 2026-08-27
---

## The defect

EliteaAI/elitea-testing-public#1279. Adding **two version-carrying participants** (Agent and
Pipeline) to one conversation drops the second one, silently. Confirmed independently three
times now — ELITEA-2455 (2026-08-26, 16 reps) and ELITEA-2094 (2026-08-27, 7 reps).

| Variant | 2026-08-27 result |
|---|---|
| Agent → Pipeline | 0/4 |
| Pipeline → Agent | 0/2 |
| Pipeline alone (control) | **1/1 OK** |

## Three things worth remembering

1. **Not order-dependent.** Any "add them in the reverse order" workaround is retired.
2. **The console is CLEAN on every drop** — no 400, no TypeError, no toast. A
   "no console errors" assertion cannot detect this. (The `version/prompt_lib` 400 on
   #1279's body fires only on runs that *succeed*.)
3. **No honest settle condition exists.** Every product-observable signal (row visible,
   `chat-switch-participant-button` visible, `networkidle`) is already satisfied at the
   instant of the drop. Only a fixed wall-clock delay changes it — banned here, and only
   ~75% reliable anyway.

## Consequence for analysis

Any case whose core is "all four participant types coexist in four sections" is **blocked**,
not soft-assertable: the four-section state has never been observed, so soft-asserting
produces a cascading multi-assertion red rather than the single deterministic signature the
sanctioned-RED exception is written for. Blocked cases: ELITEA-2094, ELITEA-2455.

**Unblock probe, ~4 min:** 6 reps of Agent→Pipeline with no fixed delay. Six greens = fixed.
Toolkit/MCP adds are unaffected and stay reliable.

Related: [[chat_participant_row_testid_absent_when_misconfigured]]
