---
name: Skill Publish AI gate rejects blanket reply instructions
description: publish_skill_validate's AI content-quality check flags "reply X to any prompt"-style instructions as prompt-injection, returns 422/FAIL — use bounded, task-specific fixture instructions instead
type: feedback
---

## What happens

The Publish wizard's Preparation→Continue step (`publish_skill_validate` /
`publish_validate`) runs an AI content-quality check on the skill/agent's
instructions. A common short fixture pattern used ELSEWHERE in the suite —
`"...Reply 'ok' to any prompt."` (fine for chat/edit tests that never touch
Publish) — trips this gate's prompt-injection heuristic:

```
critical_issues: [{"field": "instructions", "issue": "Contains a blanket
instruction to reply 'ok' to any prompt, which overrides user intent and
functions as an unsafe prompt-injection style directive.", ...}]
status: "FAIL", validation_token: null
```

`publish_skill_validate` returns `422` with `status: "FAIL"` and a null
`validation_token` — any test needing a WARN/PASS validation result (to
reach the Validation step, capture a real token, etc.) breaks here.

## Fix — use bounded, task-specific instructions

Proven-working pattern (confirmed live, from the sibling ELITEA-2595/96/98
implementation and reused for ELITEA-2597):

```python
INSTRUCTIONS = (
    "You are a QA regression assistant for the ELITEA platform test suite. "
    "When asked about a failing automated test, analyze the described "
    "symptom, summarize the most likely root cause, and suggest the next "
    "concrete diagnostic step. Keep every response concise and factual."
)
```

Task-specific, bounded scope, no "always respond with X" directive — passes
cleanly (WARN at worst, from the unrelated "description lacks action verbs"
deterministic check, which doesn't block).

## When this bites you

Any NEW Publish-flow fixture (Skill OR Agent — same shared `publish_validate`
family) that reuses a short filler instructions string from a non-Publish
test. If you only need >=100 chars and don't care about content, use the
pattern above rather than a generic "reply X" filler.
