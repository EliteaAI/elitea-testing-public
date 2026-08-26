---
name: Soft-assert/known-defect only covers an ISOLATED assertion — never the case's own headline subject
description: ELITEA-2182/2183 shipped ready-for-automation with expect.soft()+Known-defect for a Stop-button case where the defect (#1569) WAS the case's headline observable; live re-runs failed two different ways run-to-run. Reclassified to blocked, matching sibling ELITEA-2186.
type: feedback
---

## The trap

A soft-assert / `# Known defect: #N` pattern is a legitimate way to keep a
test green-except-one-line when the defect is ONE ISOLATED assertion inside
an otherwise-working flow (`.agents/testing.md` § Merge gate,
analysis-time-entry bullet). It is easy to over-apply the pattern to a case
whose entire headline subject IS the defect: e.g. "Stop Button Appears
During Response Generation" when the open defect is precisely about the
Stop button's own appear/click/disappear cycle misbehaving (#1569). Building
it anyway (as `ready-for-automation` + soft-assert) produced a test that
LOOKED buildable and even ran green once, but across multiple standalone
re-runs failed two DIFFERENT ways (a deterministic
`assert 1 == 0` on the Stop control's disappearance, and separately a React
"Maximum update depth exceeded" console error) — i.e. not a single, stable,
single-cause signature at all, just general instability radiating from the
same broken code path.

## The rule (`.agents/role-overrides.md` § Declared-improvisation protocol
ceiling)

A soft-assert/known-defect disposition requires BOTH:
1. The defect is one isolable step/assertion, not the case's own
   headline/core-subject observable.
2. The failure is deterministic — a single, stable, single-cause signature
   (§ Merge gate's own bar: "3/3 identical failures").

If either fails, the correct disposition is `blocked` → lead → track against
the open defect, matching whatever sibling case already sits `blocked` on
the same root cause (here: ELITEA-2186's AFS, same #1569 link, same wording
shape — copy its Status/Blocked-Steps phrasing for consistency across the
batch).

## The tell

Ask: "is the defect ONE step deep in an otherwise-working flow, or IS it
what the case title describes?" If the latter, don't soft-assert your way to
`ready-for-automation` — even if a first live run looked stable enough to
write the test. Confirm stability with a REAL re-run investigation (not just
the analyst's original 2 exploration runs) before trusting a soft-assert
shape for a headline observable; instability there surfaces as "different
failure each re-run", which is the sign the soft-assert is papering over
general brokenness, not one known deviation.

See also: sanctioned_red_soft_assert_traps.md ·
afs_authorized_soft_assertion_is_still_masking.md
