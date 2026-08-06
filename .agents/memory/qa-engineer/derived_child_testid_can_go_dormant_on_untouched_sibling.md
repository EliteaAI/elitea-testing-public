---
name: Derived child testid can go dormant on an untouched sibling section
description: A shared component that templates a child testid off a required parent/header prop can create a testid on a section the test never touches — check derived testids, not just the header, when a shared component threads a prop uniformly.
type: feedback
---

## Pattern (seen in PR #1251 / ELITEA-2392, `ai_providers_page.py`)

`ConfigurationSection.jsx` is one reusable component instantiated 7×
(`ConfigurationsPanel.jsx`). The implementer needed `sectionTestId` on ALL 7
call sites because 2 of them (Vector Storage, AI Credentials) are legitimately
"touched" only via absence assertions (`to_have_count(0)`, canon #511
extension) — sanctioned.

But `ConfigurationSection.jsx` also derives a SECOND, child testid from that
same prop: `data-testid={sectionTestId ? \`${sectionTestId}-default-selector\`
: undefined}` on its `Select.SingleSelect`, gated only by `hasDefaultSetting`
(a pre-existing, unrelated product prop) — not by whether the test asserts
that selector. Vector Storage has `hasDefaultSetting={true}`, so once that
section ever gets real configured data (currently zero for the shared test
project), `ai-providers-section-vector-storage-default-selector` will render
in the DOM with **zero references** anywhere in the page object or test —
neither a positive assertion nor an absence assertion. (AI Credentials was
clean here only because it happens to lack `hasDefaultSetting` entirely — a
product-code coincidence, not a testid-scoping decision.)

## Why it isn't obviously a violation

- It's dormant today — gated behind data that doesn't exist in the current
  test project, so nothing renders it right now.
- Suppressing it would require a SECOND boolean prop on the shared component
  just to gate testid emission per caller — worse API hygiene than the
  status quo, for a single-bit distinction.
- It is NOT a hardcoded literal string (grep for the literal value finds
  nothing in JSX) — it's produced by the same templated-from-prop mechanism
  the dynamic-testid canon sanctions.

## What to check next time

When a shared/reusable component threads ONE caller-supplied testid prop that
is REQUIRED on every call site (because some call sites need it for a
legitimate absence assertion), check whether that component ALSO derives a
SECOND testid from the same prop for content gated by a DIFFERENT,
unrelated condition (`hasDefaultSetting`, `isExpanded`, etc.). If so, walk
each call site's OTHER gating props, not just whether the header itself is
referenced — a call site can be legitimately touched (header) while its
derived child testid is not, and that gap is invisible to the standard
"is every testid referenced" sweep unless you check the derivation site too.

Judgment call, not an automatic block: reported this one as a non-blocking
finding (structurally forced by a single shared component, inert today) —
use judgment on whether the specific case is a deliberate blanket-add or an
unavoidable byproduct of prop reuse.
