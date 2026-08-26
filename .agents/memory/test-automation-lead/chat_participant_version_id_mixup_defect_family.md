---
name: Chat-participants version_id-mixup defect family
description: Any case needing an Agent AND a Pipeline as simultaneous chat participants is UNAUTOMATABLE until #1279 is fixed — check this family before re-diagnosing
type: project
---

## The family

A shared root cause — participant-state `version_id` resolution instability in the chat
PARTICIPANTS panel — surfaces under multiple symptoms. First documented during the
ELITEA-2094 investigation (PR EliteaAI/elitea-testing-public#688, still OPEN/unmerged,
R2-cap parked 2026-07-20). All still OPEN as of 2026-08-26:

- **#684** — Pipeline participant with an orphaned version crashes silently (no warning UI)
  instead of showing a misconfiguration warning like MCPs do.
- **#687** — A healthy remote MCP toolkit (no OAuth) falsely shows "Server is disconnected!".
- **#689** — Already-added-entity picker-exclusion filter intermittently fails once a
  Pipeline participant coexists (correlated with #684's trigger, NOT confirmed shared).
- **#1279** — The second Agent-or-Pipeline participant added to a conversation is
  **silently dropped**. See the hard numbers below.

## #1279 — the automation-blocking one (16-rep evidence, ELITEA-2455 re-attempt 2026-08-26)

**It is NOT order-dependent.** The issue body's original "Pipeline-then-Agent is a viable
workaround for test automation" line is **RETIRED** — do not act on it, and do not repeat
it in an AFS or dispatch prompt. Whichever of Agent/Pipeline is added *second* is dropped,
in both orders: **13 of 16 live pytest-harness repetitions.**

| Wait between adds | Result |
|---|---|
| none / `wait_for_network` | 0/6 |
| row visible + switch-participant button visible | 0/3 |
| same + `networkidle` | 0/3 |
| fixed 1500 ms sleep | 3/4 |

Three facts that make this a **block, not a soft-assert**:

1. **No observable settle condition exists.** Row-visible, switch-button-visible and
   networkidle all resolve together at ~1.7–2.2 s; measured gap to the failing second add
   was **0.00 s in 6/6**. Only raw elapsed time helps — i.e. a `sleep`, banned by
   `.agents/conventions.md`, and still only ~75% reliable.
2. **It is silent.** Failing runs have a *completely clean* console. The
   `version/prompt_lib` 400 + `icon_meta` TypeError fires only on runs that **SUCCEED** —
   it is a symptom of the working path. **Never use a console-error assertion as the guard
   for participant-add success.**
3. **Toolkit and MCP participants are unaffected** — back-to-back Toolkit→MCP adds are
   reliable (ELITEA-2203's merged spec does exactly that, green). The race is specific to
   the version-carrying Agent/Pipeline types.

## Rule of thumb

Before dispatching any chat-PARTICIPANTS case, check whether it needs an Agent **and** a
Pipeline simultaneously. If it does, it is **unautomatable today** — park it on #1279 and
don't spend an analyst run rediscovering this (ELITEA-2455/#963 cost two full passes).
A case needing only Toolkit and/or MCP participants is fine. A new symptom in this area is
likely a **sibling** (file + cross-link both ways), not a duplicate and not a fresh
unrelated bug.

Salvage pattern worth remembering: when a multi-participant case is blocked, check whether
its *headline objective* survives on the Toolkit/MCP-only path — ELITEA-2455's step 20
(misconfiguration warning, via `github_toolkit_with_invalid_credential`) does, and was
filed as #1823 for a human to scope into a narrower TMS case.
