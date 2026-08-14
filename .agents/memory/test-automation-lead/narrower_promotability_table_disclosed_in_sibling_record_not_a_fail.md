---
name: Narrower promotability table disclosed in a sibling record is not a FAIL
description: when a closure record's own testid table is a real subset of the merged test's full call-chain dependencies, it's not an item-3 FAIL as long as every listed row is correct AND the full set is already accurately disclosed in an explicitly-cited sibling issue's own closure record — confirmed twice same-day (#240, #260)
type: feedback
---

A shared covering test extended across several TMS cases (ELITEA-1824 → 1827 →
1835, one test method growing case-by-case) means each extending case's own
closure record can legitimately choose to report only the testids ITS OWN diff
adds/touches, or the "unchanged, inherited" set in short form — rather than
re-deriving and re-pasting the full historical dependency table every single
time.

**The check that matters:** re-derive the FULL testid set from the merged test's
own complete call chain (every page-object method/field it actually calls, not
just what the diff touches) independently, then check two things:

1. Does the closure record's own table contain any row that CONTRADICTS ground
   truth? (wrong main/testids status, wrong commit SHA) — that's still a hard
   FAIL, always.
2. If the record's table is merely a SUBSET of the full set, is the full set
   already accurately disclosed — with correct SHAs — in a sibling issue's own
   closure record that this record explicitly cites as the source of its
   inherited rows? If yes, it's not a fresh violation.

Confirmed twice on the same day (2026-07-20): #240 (ELITEA-1827/PR#658, 11-of-19
rows, citing ELITEA-1824/#228 as the source) and #260 (ELITEA-1835/PR#675,
15-of-19 rows, citing both #228 and #240/#658). Both times, independently
re-deriving the full 19-testid set found the SAME omitted rows, and both times
tracing back to #228's own closure record found it already carries all 19 with
correct SHAs. Neither record contradicted ground truth on any row it did list.

**Don't apply this leniently** — it requires ALL of: (a) every row actually
listed is independently re-verified correct, (b) the record explicitly names the
sibling issue(s) it's inheriting from (not a bare "pre-existing" with no
pointer), and (c) that cited sibling record, when checked, genuinely does carry
the full accurate set. If any of those three fail, treat it as an ordinary
incomplete-table finding instead.

This does NOT excuse the underlying pattern — it would still be preferable for
every closure record to carry the full derived set every time (cheaper for a
future reader/auditor than chasing a citation chain across 2 issues). Flagged as
a standing-watch item, not escalated to a canon-fix question yet since it hasn't
caused an actual FALSE claim in either occurrence.
