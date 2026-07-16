---
name: Orphan testid vs. wired-but-uninvoked testid
description: When auditing item 2's blanket-testid clause, distinguish a testid with zero consuming code from one wired into a real (just uncalled) method — only the latter is genuinely ambiguous enough to need a fresh question
type: feedback
---

The team ruling (2026-07-14) behind checklist item 2 says "testids on elements
the test never touches = FAIL." Two shapes both violate the letter of that
rule, but they carry very different weight when deciding whether to solo-FAIL
or file a `question`:

1. **Wired-but-uninvoked** (`#511`'s shape) — the testid is passed through to
   a real, callable page-object method that genuinely exists in the diff, but
   that specific method is never called by *this* case's test. There's a
   plausible "reusable page-object scaffolding" argument (the object may
   already serve multiple cases). Genuinely murky — worth a `question` if no
   existing one covers it.

2. **Orphan** (issue #65's `close_button`/`cancel_button` shape) — the
   testid is declared as a `LocatorDescriptor` field (or base-class
   placeholder) but **no method anywhere in the diff ever references it** —
   not even an uncalled one. There's no scaffolding argument because there's
   no scaffold. This is the plain-wording case the rule was written for.

**Practical rule:** grep for `<field_name>\.` (a method actually touching the
attribute) across the whole diff, not just `<field_name> =` (the declaration).
Zero hits anywhere = orphan = solo-FAIL, no question needed — especially if an
open question already exists for the *murkier* wired-but-uninvoked shape and
recommends "no carve-out" (as #511 does): an orphan is a fortiori covered by
that same recommendation, so don't file a third overlapping question for a
case that's strictly clearer-cut than the one still open.

## Case history

- Issue #85 (ELITEA-1907, PR #543/EliteaUI#570): `generate-agent-resource-section-title-`
  declared, never referenced. Orphan shape, solo-FAIL.
- Issue #94 (ELITEA-1929, PR #548/EliteaUI#572): `toolkit-detail-discard-button`
  declared as `detail_discard_button`, never referenced by any test/page-object
  method (`grep -rn 'detail_discard_button' automation/ --include='*.py'`
  matched only its own definition). The AFS had speculatively grouped
  "Save/Discard" together in its testid-gap note, but the implemented case
  only exercised Save — worth watching for: an AFS that names a *pair* of
  elements in its gap note doesn't mean both need testids if the case only
  touches one. Orphan shape, solo-FAIL, sibling (`toolkit-detail-save-button`)
  in the same PR was correctly wired and used — the FAIL is per-testid, not
  per-PR, don't let one compliant sibling launder an orphan one.
