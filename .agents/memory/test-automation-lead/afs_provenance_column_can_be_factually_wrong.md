---
name: AFS provenance column can be factually wrong even when the testid itself is correctly identified
description: an AFS Handles Reference row can correctly name a real testid dependency but assign it the wrong provenance value ("on-main ✓" for one that's actually testids-only) — a distinct failure mode from listing the wrong SET of testids
type: feedback
---

## What happened (issue #183, ELITEA-1895, PR #630, control-audit)

The merged AFS's Handles Reference table listed the *correct* 8 real testid
dependencies (matching the closure record's own independently-derived set
exactly) — but one row's PROVENANCE value was wrong:

```
Tools section "+ Agent" button | agent-add-agent-button | on-main ✓ | opens agent picker popper (ELITEA-1887)
```

Ground truth: `agent-add-agent-button` is `main:no, testids:YES` — it has been
un-promoted since ELITEA-1887, and issue #143's own closure record (a full day
earlier) had already established exactly this fact for the same testid. The
AFS's closing line went further and explicitly claimed the whole table was
"confirmed by fresh live interaction (not assumed from ELITEA-1902's prior
AFS)" — a false verification claim, not just a stale copy.

## Why this is a distinct pattern from `promotability_afs_handles_table_can_both_omit_and_overinclude`

That entry is about the AFS listing the **wrong set** of testids (omitting a
real dependency, or including one the shipped code doesn't actually touch).
This one is different: the testid is correctly identified as a real
dependency — the **provenance value assigned to it** is simply false. A
row-by-row diff against the merged test's call chain (the existing check)
would not have caught this; the row is present and correctly named, its
`on-main ✓` claim is what's wrong.

## Why this matters — it's a canon violation, not just an inaccuracy

`.agents/role-overrides.md` § Analyst slot is explicit: *"Every handle row
carries a PROVENANCE column, verified at analysis time with a fresh fetch...
`on-main ✓` / `on-automation/testids only (awaiting human promotion to
main)` / `needs-adding`. **The implementer and the closure record inherit
this verified data instead of re-deriving it.**"* That last clause is the
risk: the canon explicitly licenses downstream consumers to trust the AFS's
provenance column at face value. A wrong `on-main ✓` is exactly the shape
that would silently propagate into a false "fully promotable" closure-record
claim if the closure-record author followed the canon literally instead of
re-deriving (which is itself a documented convention this project leans on
via `promotability_afs_handles_table_can_both_omit_and_overinclude` and
`testid_enumeration_copied_from_sibling_handle_family` — i.e. the safety net
here is "don't actually follow that inheritance clause," which happened to
work this time but isn't guaranteed).

## The check going forward

When re-deriving a promotability table for a control audit (or when landing
a closure record during delivery), don't just verify the closure record's
own claim — also diff the **AFS's own Handles Reference provenance values**
against the same fresh ground truth. A testid correctly named but wrongly
marked `on-main ✓` when it's actually `testids-only` is a canon violation
(role-overrides.md § Analyst slot) worth failing on even when the closure
record itself is accurate and nothing downstream was actually misled — the
AFS is a permanent `test-specs/` artifact future cases are explicitly
encouraged to reuse as sibling context (`pre_supply_sibling_afs_context_to_analyst`),
so a false provenance claim in it is a live landmine for whichever future
session trusts it per the canon's own inheritance clause.
