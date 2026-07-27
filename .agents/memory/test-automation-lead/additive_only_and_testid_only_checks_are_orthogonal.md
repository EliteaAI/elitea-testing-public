---
name: Additive-only and testid-only checks are orthogonal
description: An implementer's clean additive-only self-check (no removed lines) does not imply the testid-only-handle rule also passed — a new raw locator is an addition, invisible to a diff-removal check
type: feedback
---

## What happened (ELITEA-1899 / issue #103 / PR #567)

The implementer self-verified additive-only discipline on two edited page-object
files (`git diff <file> | grep -E '^-[^-]'` → empty) and reported this as evidence
the PR was clean. It was true, and it was also irrelevant to a different rule the
same PR broke: two brand-new raw non-testid locators
(`self.agent_icon_button.locator("img")`, an inline
`card.locator('[data-testid="entity-card-icon"] img')`) had been added — not
modified, not removed anything — so the additive-only grep had nothing to flag.

A fresh reviewer caught it on the first pass via the project's separate mechanical
gate (`.agents/workflow.md` § Review gates: grep the diff for added
`get_by_role|get_by_label|get_by_text|page.locator|.locator(` lines, each hit must
resolve to a `[data-testid=` selector).

## Why this matters

Additive-only answers "did we break something that already worked" (regression
safety on shared callers). Testid-only answers "did we add something that violates
locator policy" (new-code quality). Both checks read the same diff but look for
opposite signals — removed lines vs. added lines — so passing one says nothing
about the other. An implementer (or an orchestrator sanity-checking implementer
claims) who treats "additive-only passed" as "the diff is clean" will wave through
exactly this class of defect.

## Rule

Run both checks independently on every automation PR touching `automation/pages/`
or `automation/tests/`, regardless of which one the implementer already claims to
have run:

1. Additive-only: `git diff <file> | grep -E '^-[^-]'` → should be empty (no real
   removals on a shared-caller file).
2. Testid-only: `git diff <base>...<head> -- automation/pages/ automation/tests/ |
   grep -E '^\+.*(get_by_role|get_by_label|get_by_text|page\.locator|\.locator\()'`
   → every hit must resolve to a `[data-testid=` selector, directly or via a
   class-level constant it references.

Neither implies the other. Both are cheap; run both.
