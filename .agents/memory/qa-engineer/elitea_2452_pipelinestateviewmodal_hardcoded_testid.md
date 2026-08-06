---
name: ELITEA-2452 PipelineStateViewModal hardcoded feature-scoped testid
description: src/components/ single-consumer component got 4 literal testids hardcoded instead of caller-supplied testId props — CHANGES_REQUESTED per PR #581 ruling, even with a "not really shared in practice" AFS justification.
type: feedback
---

## What happened (PR #1272, ELITEA-2452, branch tests/2452-run-details-state-before-after)

The implementer added 4 testids directly inside `src/components/PipelineStateViewModal.jsx`
(root `Dialog`, header, close button, content) as literal strings —
`pipeline-run-details-value-modal(-header|-close-button|-content)` — hardcoded
in the component's own JSX, not threaded via a `testId`/`<part>TestId` prop
from the caller (`RunStateDialog.jsx`).

This is squarely the anti-pattern named in `.agents/role-overrides.md` §
Reviewer slot / `.agents/testing.md` § Locator policy (PR #581 ruling): "A
component under `src/components/` or `src/[fsd]/shared/` gets either a
GENERIC testid or a caller-supplied `testId` prop wired at the feature's call
site" — feature-scoped literal testid hardcoded in a shared-path component is
`CHANGES_REQUESTED`, full stop.

**The AFS pre-emptively argued an exception**: "Only consumer is
`RunStateDialog.jsx`, so a feature-scoped literal testid is fine (not a
cross-feature shared component in practice, despite living under
`src/components/`)." This does NOT hold — the rule has no single-consumer
carve-out (unlike the genuine #579 third-party-widget exception, which does
list concrete conditions). Ironic tell: the SAME commit correctly used the
caller-prop pattern for `StateItemViewHeader` (`testId` prop, feature-owned
path) and `BasicAccordion` (`items[].testId`, already-wired shared
component) — so the implementer *knows* the pattern, just didn't apply it to
`PipelineStateViewModal.jsx`.

## Reviewer takeaway

When a diff touches ANY file under `src/components/` or
`src/[fsd]/shared/`, check literal `data-testid="..."` strings specifically
(not just the mechanical grep for raw Playwright locators in the *test*
repo — this is a testid-*placement* check on the *EliteaUI* diff). A
"single consumer today" argument in the AFS is not licence to skip it; the
fix is trivial (thread the same `testId` prop pattern already used
elsewhere in the same commit) so there's no real cost to requiring it.

## Re-review (fix round 1) — CONFIRMED FIXED, APPROVED

`EliteaAI/EliteaUI@0f55411b` threads `testId`/`headerTestId`/
`closeButtonTestId`/`contentTestId` props (default `undefined`) into
`PipelineStateViewModal.jsx`, wired from `RunStateDialog.jsx`'s call site
with the same literal values — exactly the pattern already used for
`StateItemViewHeader`/`BasicAccordion` in the same original commit.
Verified by reading the diff directly (`git show 0f55411b`), not by
trusting the implementer's memory/PR-body claim.

**New tell caught this round, non-blocking**: the Python page object
(`automation/pages/pipeline_detail_page.py:855-856`) still carries the
OLD comment — "feature-scoped literal testids (single consumer,
RunStateDialog.jsx)" — describing the pre-fix shape. It wasn't touched by
the fix-round commit (JSX-only fix, page object needed no locator changes
since testid *values* didn't change) so the comment now contradicts the
actual code. Doesn't affect compliance (the `LocatorDescriptor(testid=...)`
lines are still correct — comments aren't locators) but it's a landmine:
a future reader could cite this stale comment as precedent for hardcoding
a literal testid in a shared component, recreating the exact mistake this
entry documents. **Checklist addition**: after confirming a JSX-side testid
fix, grep the PAIRED page-object file for comments describing the OLD
shape too — a fix round that only touches one repo can leave the other
repo's prose stale even when its code is already correct.
