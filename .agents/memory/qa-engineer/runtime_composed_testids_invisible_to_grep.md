---
name: Runtime-composed testids are invisible to a literal grep — check the template line
description: A shared component building data-testid from a prop makes the concrete value ungreppable; conclude "needs adding" only after reading the component.
type: feedback
aliases: [select-option testid, composed testid, grep blind spot, provenance false negative]
tags: [area/ui, type/provenance]
created: 2026-08-27
updated: 2026-08-27
---

## The false negative

`git grep 'select-option-days' origin/main -- src/` returns **nothing**, yet the
testid is live in the DOM. The shared select builds it at runtime:

```jsx
// src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx:117
data-testid={option.testId ?? `select-option-${option.value}`}
```

So a provenance check that stops at the literal string reports `needs-adding`
for a testid that has been on `main` all along — and the implementer then does
pointless EliteaUI work, or worse, rungs down to a raw handle.

## The check that works

When a handle comes from a **shared** component, grep the **template**, not the
value: search for the prefix plus a backtick/`${`, or open the component and read
the attribute. Then verify the template line on both refs:

```bash
git grep -n 'select-option-${option.value}' origin/main origin/automation/testids -- 'src/**/SingleSelectMenuItem.jsx'
```

This is the same stage-1 blind spot `.agents/workflow.md` § Closure record
documents for closure records — it bites **analysis** provenance rows just as hard.

Compliant page-object shape for such a handle is the class-level template
(`OPTION_SELECTOR = '[data-testid="select-option-{}"]'`), never an inline f-string.
