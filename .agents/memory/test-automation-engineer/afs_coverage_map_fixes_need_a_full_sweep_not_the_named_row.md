---
name: AFS Coverage Map fixes need a full sweep, not just the named row
description: ELITEA-1839/PR #639 — fixing only the reviewer-named Coverage Map row (round 1) left the identical overclaiming pattern in 3+ sibling rows, causing a round-3 bounce; when a Coverage-Map "Asserted where" cell is found wrong, treat it as a signal to re-tick every row against the shipped code, not a one-line patch
type: feedback
---

## The mistake (round 1, mine)

PR #639 (ELITEA-1839, download-single-file-via-dropdown) round-1 review found
one Coverage Map row (Step 2) whose "Asserted where" cell described a
breadcrumb assertion that doesn't exist in the shipped test — the analyst's
live-exploration observation had been carried into the cell verbatim instead
of the coarser proxy (`file_exists()` + `file_count == 1`) the implementation
actually uses. I fixed exactly that one row (commit `9de3e191`) and moved on.

## The bounce (round 2, a fresh reviewer)

A fresh round-2 reviewer re-ran the FULL Coverage Map checklist (not just the
named delta) and found the identical class of mismatch surviving in 3 more
rows, sitting immediately adjacent to the one I'd fixed:
- Step 1's row also claimed a nonexistent breadcrumb assertion.
- Step 3's row claimed Type/Size assertions the code never makes (only
  `file_exists()` + count).
- Step 5's row claimed an exact `["Download","Delete"]` list-match; the code
  does two independent, strictly weaker `to_be_visible()` checks.

## What a proper full sweep then found (round 3, mine)

Doing the sweep the second reviewer's finding demanded — every Axis-1 AND
Axis-2 row, re-checked line-by-line against `test_artifacts_download_single_
file_dropdown.py` + `artifacts_page.py`, not just the 3 named rows — turned
up a FOURTH, previously unflagged instance of the same pattern: Step 7's row
cited "screenshot immediately post-click shows zero dialog elements" (the
analyst's live evidence) instead of the actual shipped
`expect(zip_download_progress_dialog).to_have_count(0, ...)` assertion.
Three reviewer-named rows would have still left one mismatch in the table
after a third "fix the named rows" pass.

## The generalizable lesson

When a reviewer finds a Coverage-Map cell that describes what the analyst
observed live rather than what the shipped test asserts, that is a SIGNAL
about the AFS's authoring process, not an isolated typo. The analyst pass and
the implementer pass usually diverge in the same direction across an entire
table (analyst chases the richest observable; implementer picks a cheaper,
coarser, more stable proxy) — so the mismatch is a property of the table, not
of one row. Fix scope should default to "sweep the whole Coverage Map" the
FIRST time this class of finding lands, not the second or third. Concretely:
grep the shipped test/page-object for every literal claim in every
"Asserted where" cell (breadcrumb text, exact list-matches, field values like
Type/Size) before considering the AFS accurate again.

## Severity note

None of these mismatches were case-compliance failures — the underlying case
requirement was still met by a coarser real assertion in every instance. This
is purely Coverage-Map-traceability accuracy, but it's still a legitimate
CHANGES_REQUESTED/bounce-worthy class: a Coverage Map that overclaims what's
asserted defeats its own purpose (a future reader can't trust it to know what
the shipped test actually locks in).

## Addendum (ELITEA-1824/PR #653, round-3) — the same pattern from a NEW cause

ELITEA-1839's lesson above is about analyst-vs-implementer divergence. This
round found the identical symptom (Coverage Map / Concrete Handles rows
stale relative to the shipped code) from a different root cause: **my own**
prior-round AFS amendment was incomplete. That round's Phase 2 exploration
added 5 testids to close AFS-documented gaps; the PR description and the AFS
amendment both narrated only 2 of the 5 (the ones top-of-mind while writing
the summary), leaving the other 3 (`artifacts-upload-files-empty-state-
button`, `data-selected`, the two breadcrumb-label testids) still reading
"none"/"testid needed" across 9 separate spots (3 Concrete Handles rows, 5
Coverage Map rows, 6 Test-Step inline bodies) even though they were fully
wired and asserted. Same fix shape as before — grep every literal handle
string across the WHOLE document rather than trusting the named 3 — but the
trigger this time was self-authored incompleteness, not analyst/implementer
drift. **Generalized rule: whenever a single PR round's Phase 2 exploration
adds/changes N handles, grep for all N handle strings across the entire AFS
before writing the PR description** — narrating only the ones that come to
mind while summarizing is exactly how a partial amendment ships and bounces
on the next fresh-reviewer pass.
