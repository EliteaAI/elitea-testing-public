---
name: HITL tool chip renders at the CALL ATTEMPT, not at execution
description: chat-answer-tool-chip is present while the authorization card is still pending — an absence assertion on it can never pass
type: feedback
aliases: [tool chip, chat-answer-tool-chip, execution chip, ActionView chip]
tags: [area/chat, area/hitl, type/locator-semantics]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

`chat-answer-tool-chip` (`EliteaUI/src/components/Chat/ActionView.jsx:407`,
`data-testid={toolkitType === 'model' ? 'chat-answer-model-chip' : 'chat-answer-tool-chip'}`)
is rendered from the **tool-call action** with no execution predicate. Verified live
2026-08-27, ELITEA-2213, two independent runs:

- count **1**, text `{toolkit_name}: {tool_name}`, **while the Sensitive Action
  Authorization card is still pending and before any decision is clicked**
- count **1** still, after Block
- count **0** after a page reload — the chip is a live-stream render, not persisted

## Why it matters

Any case whose text says "verify no tool EXECUTION chip" cannot be automated as
`expect(answer_tool_chip).to_have_count(0)` — that asserts a state the product never
enters. Non-execution is proven at the **backend** (e.g. `ArtifactAPI.list_bucket_files`),
never at the chip. Treat the case text as drift → CLARIFICATION, not a defect.

Canon ruling #277 shape (b) for this ternary pair is satisfied by ELITEA-2212's two
POSITIVE assertions (model chip + tool chip), so dropping an absence assertion elsewhere
does not break compliance.

Related: [[hitl_resume_drops_the_turn_on_both_authorize_and_block]]
