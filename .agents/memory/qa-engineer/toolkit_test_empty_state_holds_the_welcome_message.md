---
name: Toolkit Test surface — the "welcome message" moved, it was not removed
description: ToolkitTestEmptyState.jsx still renders the pre-run guidance text; only ToolkitTestResults returns null
type: reference
---

Reviewing the ELITEA-1866 repair (#1815) I had to disprove a plausible claim: that
the toolkit Test surface has "no welcome message any more, in any form" because
`ToolkitTestResults.jsx` does `if (!messages.length) return null`.

That is only half the component tree. On EliteaUI `origin/main`:

- `src/[fsd]/features/toolkits/ui/toolkit-test/ToolkitTestResults.jsx:29` — yes,
  returns `null` before the first run, so `chat-message-list` does not exist yet.
- `src/[fsd]/features/toolkits/ui/toolkit-test/ToolkitTestEmptyState.jsx:29,35` —
  **but this renders "Test toolkit" (or "Test MCP") + "Choose a tool from the list
  to configure parameters and run the test."** It is rendered by
  `ToolkitTestPanel.jsx:70`, and it is the SAME component that carries
  `data-testid="toolkit-test-empty-tool-select"` — the handle the automation
  already asserts on at that step.

So the pre-run guidance text is **relocated + reworded**, not deleted. It has no
testid on the `Typography`, which under `.agents/testing.md` § Locator policy is
work to do (`add-data-testid`), never grounds to declare the observable gone.

Generalisable trap: "component X early-returns null" proves the observable is
absent **from X**, not from the surface. Before accepting a "the product removed
it" claim, grep the product for the TEXT, not just the component the previous
implementation happened to read it from — the sibling component two lines away in
the same panel is exactly where a redesign puts it.
