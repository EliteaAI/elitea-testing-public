---
name: AFS status defect-found can still route as extend-existing + sanctioned-RED
description: an AFS's own Status header of defect-found doesn't automatically mean "park automation" — if the analyst's own writeup shows the defect is isolated (not blocking) and most of the case is already covered, check SKILL.md's actual Phase-1 table (defect-found is conditional-accept for isolated defects) before treating it as a parked case
type: feedback
---

## What happened (ELITEA-1799, issue #148, PR #608)

The analyst's AFS set `Status: defect-found` for ELITEA-1799, and its own
"Board Search Confirmation" section explicitly reasoned that defect-found
"takes precedence for the overall classification." Taken at face value,
Critical Rule 3's shorthand ("defect-found → route the filed bug through
the bug pipeline; parked automation resumes after the fix") would suggest
parking the whole case.

But the AFS's own body told a different story: steps 1-9 and 2 of 3
Expected-Final-State clauses were already behaviorally covered by an
existing merged test (same traceability-gap shape as several already-merged
sibling cases in the same module) — only ONE clause was blocked by an
isolated (not blocking) defect. `SKILL.md`'s actual Phase-1 Absorb table
(the stated single source of truth) has a `defect-found` row that is
**conditional-accept**, not automatic-park: "Confirm the defect ticket
exists AND the AFS specifies handling (expect.soft() for isolated,
let-it-fail-naturally for blocking)." My own memory
(`isolated_defect_red_is_expected.md`) already establishes that isolated
defects proceed through implementation with soft-assert handling, not park.

## The lesson

When an AFS's Status header says `defect-found`, don't stop at the header —
read whether the analyst's own evidence describes the defect as *isolated*
(rest of the flow works) or *blocking* (can't get past a step). If isolated
and most of the case is otherwise already-covered/extend-existing-shaped,
route it as such: dispatch the implementer with `extend-existing` mechanics
plus a soft-assert Gap assertion for the isolated defect, rather than
parking the whole case waiting on the bug fix. Cross-check the AFS's own
recommended *handling* for the defect against project policy too (see the
companion entry `isolated_defect_can_ship_green.md`) — the header can be
wrong on both classification and prescribed handling at once.
