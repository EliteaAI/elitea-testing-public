---
name: LLMModelSelector two variants — verify actual render, not just source
description: LLMModelSelector.jsx has a 'field' and a default variant with DIFFERENT testids on the settings button; source-reading alone can pick the wrong one
type: feedback
---

`EliteaUI/src/[fsd]/widgets/llm-model-selector/ui/LLMModelSelector.jsx` renders
TWO structurally different layouts from one component, switched by a `variant`
prop:

- `variant === 'field'` — a vertical field-style layout (used e.g. by Toolkit
  Index History). Its gear/settings button had NO testid before ELITEA-2179/2466
  added one there.
- default (non-`'field'`) — the `ButtonGroup` layout the CHAT composer actually
  uses (`NewChatInput.jsx` calls `<LLMModelSelector>` with no `variant` prop).
  This branch's gear/settings button ALREADY carries
  `data-testid="model-settings-button"`, with zero prior page-object callers
  (canon #511 first caller) — i.e. it was pre-existing, unused, and easy to
  miss on a source-only read because the `'field'` branch you're looking at
  first has no testid at all, tempting you to add one right there.

**Lesson: after finding "no testid" on a source read, confirm which JSX BRANCH
the page you're actually testing renders before adding one** — grep/read
alone can land you on the wrong variant of a multi-variant shared component.
`document.querySelectorAll('[data-testid="..."]').length` against the live
dev server (or a Playwright snapshot) settles it in one call. Caught and
reverted same-session on ELITEA-2179/2466 before it shipped as dead
instrumentation (`EliteaAI/EliteaUI@293d3aee`).
