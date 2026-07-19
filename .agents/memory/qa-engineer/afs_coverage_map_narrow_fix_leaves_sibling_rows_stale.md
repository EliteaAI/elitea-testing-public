---
name: AFS Coverage Map narrow fix leaves sibling rows stale — check the whole table, not just the named row
description: PR #639/ELITEA-1839 round-2 finding — a round-1-requested AFS Coverage-Map correction fixed exactly the one row named in the finding but left the identical class of inaccuracy in 3 more rows; always re-tick every Axis-1 row's "Asserted where" text against actual code, not just the row a prior review named
type: feedback
---

## The pattern

`test-specs/artifacts/l2_download-flow-single-file-actions-dropdown_ELITEA-1839.md`'s
Coverage Map Axis 1 has an "Asserted where" cell for every case step. The analyst
wrote these DURING LIVE EXPLORATION (page.evaluate reads, screenshots, manual
observation) — richer detail than what usually ends up in the shipped automated
test, which typically asserts a coarser, cheaper proxy instead.

Round-1 review of PR #639 caught exactly one instance of this drift: Step 2's row
claimed "Breadcrumb shows `{bucket} > a1`, confirmed live" as the asserted
evidence, but no breadcrumb locator/assertion exists anywhere in the shipped
`ArtifactsPage`/test — the actual code proves "subfolder selected" via a
`file_exists()` + `file_count == 1` proxy instead. The implementer's round-2 fix
(`9de3e191`) corrected **that one row** with an honest, detailed explanation of
the proxy relationship.

Round-2 review (fresh session, ran the full standing checklist rather than just
verifying the named delta) found the IDENTICAL class of inaccuracy still present
in three more rows of the same table:
- Step 1's row still claimed "Breadcrumb + file table render" — same
  nonexistent-breadcrumb problem, immediately adjacent to the row that got fixed.
- Step 3's row claimed "File row present, Type 'Text', Size '46 B'" — the code
  only ever asserts file-name presence (`file_exists()`) and total count; Type
  and Size columns are never read or asserted anywhere.
- Step 5's row claimed an exact-list match (`[role="menuitem"] text content =
  ["Download", "Delete"]`) — the code only does two independent
  `to_be_visible()` checks per item, which would still pass if a third,
  unexpected menu item were present. Not an exhaustive/exact-count check.

## Why this happened

The implementer fixed the SYMPTOM the reviewer named (one specific row) instead
of recognizing the GENERAL pattern (any Coverage-Map row whose "Asserted where"
text was authored from analyst-pass live-exploration observations, then never
updated when the implementer chose a coarser/cheaper proxy assertion for the
shipped test). A row-scoped fix looks complete in isolation — it resolves the
literal finding — but doesn't audit siblings with the same root cause.

## Reviewer technique this validates

When a fix lands for "AFS row X doesn't match the code," don't just verify row X
now matches. Grep for the SAME kind of claim across every other Axis-1 row in the
same table (in this case: `grep -in breadcrumb`, then manually cross-checking
"Type"/"Size"/"exact list" claims against the actual test body line-by-line) —
the fix author had exactly the same blind spot for the sibling rows as they did
originally for the one that got caught.

## Severity calibration

None of these 3 gaps are case-compliance failures — the TMS case's own literal
wording for those steps ("subfolder selected," "sample.txt visible," "both
options visible") is still satisfied by the coarser assertions that DO exist.
This is purely a Coverage-Map-traceability-accuracy problem: a future reader
trusting the Map's "Asserted where" column to know what the shipped test locks
in would be misled. Still rated Important/blocking (CHANGES_REQUESTED) for
consistency with round 1's identical-class finding — leaving 3 unfixed instances
of a category just fixed once isn't "resolved."

## Resolution (ROUND 3, closed out APPROVED)

The round-2 finding named 3 rows explicitly, but round 3's actual fix instruction
(from the requesting agent, not just the implementer's own initiative) was framed
as "sweep the WHOLE Coverage Map," not "fix these 3 rows." The implementer found
and fixed a 4th, previously-unflagged row of the identical shape (Step 7 — cited
the analyst's screenshot evidence instead of the real
`expect(zip_download_progress_dialog).to_have_count(0, ...)` code assertion) that
neither round 1 nor round 2 had named. Round 3 review independently re-derived
all 13 Axis-1 rows + both Axis-2 entries from the actual test code from scratch
(not just re-checking the 4 named rows) and found zero remaining instances of the
pattern. Verdict: APPROVED.

**Confirms the general lesson**: a fix instruction scoped to "the named row(s)"
reliably reproduces this exact narrow-fix failure mode across rounds (round 1→2
proved it once already). A fix instruction scoped to "the whole table/pattern"
is what actually closes out a Coverage-Map-accuracy finding class in one round
instead of playing whack-a-mole across N+1 reviews. When requesting a fix for
this finding shape in the future, say "sweep the whole map for this pattern,"
not "fix row X" — the latter phrasing is what caused rounds 1 and 2 to each
leave siblings behind.
