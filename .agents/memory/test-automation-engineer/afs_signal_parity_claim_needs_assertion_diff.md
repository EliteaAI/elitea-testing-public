---
name: AFS signal-parity claim needs an assertion diff, not a prose match
description: When Axis-2 claims "matches the covering spec's N-signal pattern", diff the actual assert list against the covering spec's — a copied description text is not a copied assertion set.
type: feedback
---

## What happened

ELITEA-2459 (`extend-existing` on ELITEA-2458's covering spec) shipped with an
AFS Axis-2 claim: "Both steps assert the click-has-no-effect claim via the
same THREE-independent-signal pattern the covering spec established (editor
stays open, input value unchanged, no PUT fires)". The prose matched the
covering spec's own docstring almost word for word.

But the shipped code only had TWO of the covering spec's three signals:
`folder_name_input.is_visible()` + input value unchanged + no PUT — missing
`chat.get_folder_item(folder_id).count() == 0` (the covering spec's
"editor stays open" is a COMPOUND check: visible AND zero-count on the
accordion row, because `FolderAccordion.jsx` only re-mounts when NOT
editing — a single `is_visible()` on the input can pass even if the
component unexpectedly remounted underneath it). Reviewer caught it in
round 1; the AFS text and the code had silently drifted apart despite
reading identically at a glance.

## The check

Whenever an AFS (or your own draft) claims parity with a covering spec's
established pattern — "same N-signal check", "same 3-part assertion",
"matches precedent" — don't trust the prose. Actually list the covering
spec's asserted lines for that block and diff them 1:1 against what you
wrote:

```bash
grep -n "assert " <covering-spec-block> > /tmp/covering.txt
grep -n "assert " <new-spec-block> > /tmp/new.txt
diff /tmp/covering.txt /tmp/new.txt
```

A prose description surviving a copy/paste is not evidence the assertion
set survived it too. This is the same discipline as
`afs_is_a_work_order_not_gospel.md` but pointed at your OWN draft's claims,
not just the analyst's — self-authored Axis-2 additions need the same
verification the covering spec's claims get.
