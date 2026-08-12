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

## Second confirmed trigger shape (ELITEA-2599): coercive "MUST/Do NOT" + forced case-transformation

A DIFFERENT fixture pattern — the coercive-imperative style
`test_skill_agent_interaction.py` uses for its (never-published) chat-only
skills — ALSO trips the same gate, with a distinct critical_issues message:

```
"CRITICAL: You MUST convert ALL text in your response to UPPER CASE
letters. Do NOT use any lowercase letters. Do NOT explain or interpret
the text - just output it in UPPER CASE. ..."
→ critical_issues: [{"field": "instructions", "issue": "Contains a
prompt-injection style directive that attempts to override normal
assistant behavior by forcing all-uppercase output and prohibiting
explanation.", ...}]
```

If you need a Publish-flow fixture that ALSO needs a deterministic,
programmatically-verifiable chat-response marker (e.g. testing that an
agent still applies a skill after unpublish/republish), rewrite the same
transformation as a plain stylistic preference — no "MUST"/"CRITICAL"/
"Do NOT" language, frame it as a choice rather than an override:

```python
INSTRUCTIONS = (
    "This is a lightweight formatting skill for automated regression "
    "testing. When a user explicitly invokes this skill, respond in upper "
    "case letters as a simple stylistic choice, since upper case text is "
    "easy to verify programmatically in an automated test suite. Keep the "
    "reply brief and friendly."
)
```

Passed cleanly (confirmed live). General rule now confirmed across TWO
trigger shapes: it's not just "no blanket reply-X directives" — ANY
imperative/coercive phrasing ("MUST", "CRITICAL", "Do NOT ... just ...")
reads as prompt-injection to this gate, regardless of what the instructed
behavior actually is. Fixtures that need a deterministic marker AND must
survive Publish should be phrased as permissive stylistic preferences.

## The ≥100-char length gate applies to the AGENT's OWN instructions too, independently of any attached skill (ELITEA-2600, confirmed live)

`publish_validate` for an AGENT with attached Skills inspects BOTH (a) each
attached skill's own instructions content AND (b) the agent's own
`instructions` field — as two INDEPENDENT length checks, not one shared
budget. Seeding all attached skills at ≥100 chars is not sufficient by
itself: an 88-char AGENT instructions string (e.g. a short "you can use your
attached skills" filler) still trips `Critical Issues (1): instructions:
Instructions are too short (min 100 chars). Fix: Expand instructions
(currently 88 chars)` on its own, with `validate_status == 422`, even though
every attached skill already clears the gate. Symptom is identical in shape
to a skill-content failure (same `field: "instructions"` critical-issue
envelope) — read the `field`/message text, don't assume "skills are long
enough" rules it out. Fix: write the agent's own instructions fixture at
≥100 chars too, same as any skill fixture.
