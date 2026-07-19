---
name: Deriving the full testid-dependency set from the merged test's call chain surfaces OTHER cases' un-promoted testids too
description: A closure record's promotability check should enumerate every testid the merged test's own call chain touches, not just the current PR's new testids — this catches a DIFFERENT, already-merged sibling case's testids also still pending main, a recurring pattern worth flagging every time, not just once
type: feedback
---

On #212/ELITEA-1808/PR#643's closure record, deriving the full 16-testid dependency
set from the merged test's actual page-object call chain (not just the 8 testids new
to this PR) surfaced that 3 testids reused from ELITEA-1832/#209 (a DIFFERENT,
already-merged, `control:audited` sibling case — commit `bf008838`) are ALSO still not
on `main`. This is the same class of finding as
`promotability_must_cover_every_dependency_not_just_this_prs.md` and
`testid_enumeration_copied_from_sibling_handle_family.md`, but confirms it's not a
one-off: it's now recurred across multiple independently-audited cases (#209 itself
audited clean on item 3, #197's audit also traced multiple reused-testid commits).

**Practical technique that worked well here**: rather than trust the AFS's Concrete
Handles table (which can itself be stale/incomplete — see
`testid_enumeration_copied_from_sibling_handle_family.md`), grep the test file for
every `artifacts_page.<method>(` call, then trace each called method's body in the
page object for its `LocatorDescriptor`/class-constant testid literal — this
mechanically reconstructs the TRUE dependency set from code, independent of what any
AFS or prior closure record claimed. Cross-referencing that set against a fresh
`git fetch` + bare-string `git grep` on both `main` and `automation/testids` catches
gaps in both directions: testids this case's own PR needs to promote, AND testids a
different case still owes.

**Standing recommendation**: every closure record's promotability table should be
built this way (call-chain-derived, not AFS-copied) as the default technique, not just
when something feels off — it's cheap (a few grep + Read calls) and the sibling-case-gap
finding has now recurred enough times to be an expected outcome, not a surprise.
