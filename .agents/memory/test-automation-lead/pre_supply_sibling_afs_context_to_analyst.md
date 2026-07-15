---
name: Pre-supply sibling AFS context to analyst
description: When a new case's title/module strongly echoes an already-automated case (same shared UI component, similar flow), name the sibling AFS + implementation directly in the analyst dispatch prompt instead of letting them rediscover it
type: feedback
---

## What happened

Issue #65 (ELITEA-2001, "[skills] Build with AI generation failure/retry")
was near-identical in shape to an already-automated sibling case, ELITEA-1915
("[agents] Build with AI generation failure/retry") — same underlying shared
React component (`GenerateEntityModal.jsx`/`GenerateEntityButton.jsx`), same
functional pattern (fill prompt → mock failure → verify error+preserved
prompt → retry → verify draft), different entity type (Skill vs Agent).

Before dispatching the analyst, I found the sibling AFS
(`test-specs/agents/l2_build-with-ai-generation-failure-retry_ELITEA-1915.md`)
and its implementation myself, and named both directly in the dispatch
prompt — including the sibling's own documented testid-gap finding (at the
time it shipped, the shared component had ZERO testid props anywhere).

This let the analyst quickly discover, live, that the **shared component had
since gained full testid-prop support** (used correctly by the Agent
wrapper) but the **Skill wrapper never wired the props through** — a much
smaller, purely mechanical gap than the original agent-side one. She didn't
have to rediscover the shared-component relationship or guess what to check
for; the dispatch prompt handed her the exact comparison to make.

## Why this matters

Without the sibling context, the analyst would still eventually find the
shared component and the testid gap through her own exploration — but it
costs extra tool calls and, more importantly, risks under-investigating the
"has this changed since the sibling case?" question, since nothing prompts
her to specifically check for API/behavioral drift against a known-similar
precedent. The comparison is exactly the kind of thing a lead can spot from
a title/module match at triage time, before any exploration happens.

## Rule of thumb

Before dispatching the analyst for a new case, `grep`/search
`test-specs/**` for a title or component-name echo. If a real hit exists,
name it explicitly in the dispatch prompt: point at the sibling AFS path,
its implementation file(s), and any single documented finding (defect,
testid gap, quirk) worth checking for drift. This isn't scope creep on the
analyst's job — she still executes the case live and confirms independently
— it's giving her a sharper starting hypothesis instead of a blank one.
