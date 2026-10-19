---
name: Ask-User clarifying card is non-deterministic for Agent/Pipeline builder prompts
description: ELITEA-3372 — the ask_user clarifying card does not reliably fire for identical agent/pipeline-creation messages; automation must branch (poll for card OR direct chip), never assert one path.
type: feedback
---

## Finding (ELITEA-3372, 2026-10-19)

Live-confirmed across ~14 independent runs (fresh conversation each time,
`internal_mcp`+`ask_user` enabled, identical message text): sending
`"Create an agent for customer support"` (or close variants: `"Create an
agent"`, `"Build me an agent"`, `"I need an agent"`, `"Create an agent for
me"`) sometimes triggers the Ask-User clarifying-question card
(`ClarifyingQuestionControl.jsx`, reachable via
`get_by_placeholder("Your option")`), and sometimes the model proceeds
directly to creating the agent — no card at all, `generated-entity-chip`
appears straight away. Same message, same toggle state, same fresh
conversation shape — only the model's own routing decision varies.

Observed split: `"Create an agent for customer support"` → 2/5 card, 3/5
direct. `"Create a pipeline for data processing"` → 0/2 card, 2/2 direct
(small sample). Other agent phrasings → 5/6 card, 1/6 direct.

## Why this matters for automation

**Never write a test that asserts "the clarifying card always appears" (or
"never appears") for an Agent/Pipeline-builder creation prompt.** Any test
touching this flow must poll for EITHER outcome and branch:

```python
found_card = False
for _ in range(70):
    page.wait_for_timeout(1000)
    if page.get_by_placeholder("Your option").count() > 0:
        found_card = True
        break
    # also check for direct completion (Copy-to-clipboard button on the
    # last message) to break out of the poll loop either way
if found_card:
    # fill the custom-option textbox, click Continue (re-query — the
    # button's accessible name flips Skip -> Continue once answered), repeat
    # until the card is gone, THEN wait_for_ai_response()
```

This is the same reverse-masking class `.agents/role-overrides.md`'s
interaction-discovery ladder warns about for UI controls — asserting one
specific path every run would make the test flaky against a real, stable,
by-design LLM routing decision, not a product defect. Recommended as a
case-text CLARIFICATION on ELITEA-3372 (and any sibling case that assumes
the card always fires), not filed as a bug.

## Related

- `generated-entity-chip` (`ChatPage.GENERATED_ENTITY_CHIP` /
  `message_has_generated_entity_chip()`, added by ELITEA-3370) fires for
  `entity_type: 'agent'`/`'pipeline'` too, not just `'skill'` — confirmed
  this pass, direct reuse, no new page-object work needed.
- Full detail + evidence table: `test-specs/chat-interface/l1_builder-modules-enabled-agent-pipeline-ask-user-hitl_ELITEA-3372.md`
  § Known Defects/Clarifications; cached in `test-specs/chat-interface/_surface.md`.
