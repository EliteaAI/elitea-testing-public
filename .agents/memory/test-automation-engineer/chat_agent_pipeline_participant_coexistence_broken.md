---
name: Chat agent+pipeline participant coexistence broken (#1279)
description: Adding Agent+Pipeline as simultaneous chat participants is unreliable — check #1279 before automating any such case
type: feedback
---

Confirmed live (ELITEA-2455, 2026-08-06): adding an Agent participant THEN
a Pipeline participant to the same chat conversation is a **silent no-op**
on the Pipeline add (item clicks, network-idle completes, no error, no new
participant created). The REVERSE order (Pipeline first, then Agent) adds
both but throws a console error (`GET
/elitea_core/version/prompt_lib/{project}/{agent}/{version}` → 400 +
`TypeError: Cannot read properties of undefined (reading 'icon_meta')` at
`ChatBox.jsx:1601`) during the Agent add — and even THAT order was not
reliably reproduced 2/2 (worked via manual Playwright-MCP driving, failed
once inside the real pytest harness with identical page-object methods).

Filed EliteaAI/elitea-testing-public#1279 — sibling of the already-known
#684 (same participant-state `version_id` mixup family the parked
ELITEA-2094 investigation documented: "can crash immediately, crash later
at Send, silently misclassify a badge into the wrong PARTICIPANTS section,
or resolve with ZERO VISIBLE SYMPTOM depending on timing").

**Agent-only, Pipeline-only, Toolkit-only, and MCP-only participant adds
are all independently reliable** — this is specifically about Agent+Pipeline
COEXISTENCE.

**Before analysing or implementing ANY case that needs an Agent AND a
Pipeline as simultaneous chat participants**: check whether #1279 (and its
siblings #684/#687/#689) are still open. If so, expect the same instability
and weigh the `defect-found`/park classification ELITEA-2094 and ELITEA-2455
both reached, rather than re-discovering this from scratch. Full writeup +
Concrete Handles (testid patterns for the Agents/Pipelines submenus, none
of which need `add-data-testid` work) live in
`test-specs/chat-interface/l1_chat-create-conversation-add-all-participant-types_ELITEA-2455.md`
and `test-specs/chat-interface/_surface.md`.
