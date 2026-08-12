---
name: Pipeline embedded chat shares main chat components
description: PipelineDetailPage's embedded chat renders via the same ApplicationAnswer/ActionView/RotatingMessages chain as ChatPage — ELITEA-2181's testids transfer
type: reference
---

Confirmed live 2026-08-09 (ELITEA-2017 analysis): the pipeline detail page's
right-side embedded chat panel (`ChatPanel.jsx`) renders AI responses through
the EXACT SAME component chain as the main conversation chat
(`ApplicationAnswer.jsx` / `ActionView.jsx` / `RotatingMessages.jsx`) — the
"Thought for `<n>` secs" accordion + model-chip pattern (e.g. `GPT-5 mini
(LLM1)`) is identical to what `l2_streaming-response-progressive-display_ELITEA-2181.md`
documented for regular chat.

Practical consequence for any future pipeline-chat case: the 6 testids
ELITEA-2181 flagged `needs-adding` (`chat-answer-thought-accordion`,
`chat-answer-model-chip`, `chat-answer-loading-placeholder`,
`chat-copy-button`, `chat-regenerate-button`,
`chat-answer-pause-scroll-toggle`) are ALREADY implemented on
`automation/testids` (confirmed via `git grep` on both refs) — not yet on
`main`, but usable on localhost today. Don't re-flag them as gaps for a
pipeline-surface case; check `test-specs/pipelines/_surface.md` § "Embedded
chat panel" first.

Also noted: `PipelineDetailPage` has no `model_selector`/`select_model()`
page-object support yet. When adding it, mirror `AgentDetailPage`'s pattern
(`model_selector_button`/`model_selector_name` fields +
`MODEL_SELECTOR_OPTION_ANY_SELECTOR` dynamic-option constant) — NOT
`ChatPage.model_selector`'s, which carries a forbidden `fallback=` param
(pre-existing tech debt).

Separately: a pipeline LLM node's response can hit a "Token limit reached
mid-response. Press 'Continue' to see more." affordance intermittently on
long-response prompts (observed on 1 of 2 live runs asking for ~500-word
essays) — not an error, no console/network signal, just a max-token cutoff
with a continuation UI. Any case asserting FULL response completeness
(not just a length minimum) needs to account for this; a >200-char minimum
style assertion is unaffected since truncation happens well past that.
