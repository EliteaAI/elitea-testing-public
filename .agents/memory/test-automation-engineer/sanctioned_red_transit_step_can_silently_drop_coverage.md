---
name: A sanctioned-RED transit step that re-anchors a downstream assertion silently drops coverage
description: Re-anchoring an assertion to a transit-produced value rewrites what it proves; restore the old link with a guarded hard assert
type: feedback
---

**The pattern that bites.** Repairing a spec to merge RED on a known defect often means inserting a
transit step (a reload, a re-fetch, a second navigation) to reach the later steps, then pointing a
downstream assertion at the *new* value instead of the one the defect broke. That re-anchoring looks
mechanical. It is not — it changes what the assertion proves, and the loss is invisible in the run
output because everything is green.

Worked case, ELITEA-1899 / defect #2055 (2026-09-09, caught at review, not by me):

- Pre-repair: `card_src == new_src` — `new_src` was the header src rendered **immediately** after
  the picker selection. The assertion proved *the icon the header shows at once is the icon that
  reaches the list card*.
- Repair: #2055 made the header `<img>` absent until a reload, so Step 4's immediate read went soft,
  a transit `page.reload()` produced `persisted_src`, and Step 7 became `card_src == persisted_src`.
- What broke: nothing compared the immediate value to anything derived from the persisted one. Once
  #2055 is fixed, a header rendering icon *0* while the PUT persisted icon *3* passes the soft check
  (non-empty, changed), passes the transit assert, passes Step 7. **Green on a real bug** — and in
  the very defect class the repair was about (a broken optimistic-render path).
- Why it blocks rather than being a nit: unlike the soft asserts, this loss **does not self-heal**
  when the defect is fixed. It is permanent unless someone notices.

**The check to run on every re-anchoring:** *what did the OLD anchor prove that the NEW one does
not?* If the answer is non-empty, restore the link.

**The shape that restores it** — hard, but guarded on the old anchor being readable, so it cannot
fire during the defect window and cannot pollute the sanctioned-RED single-cause signature:

```python
if immediate_src:                      # never true while the defect is open
    assert immediate_src == persisted_src, (...)
```

Hard, not soft, deliberately: post-fix a mismatch is a **new** defect and must surface as a raw red,
never as a member of the known defect's closed set.

**Two related traps in the same repair:**

- A `!= previous_src` guard reads stronger than it is when `previous_src` is `""` on fresh data —
  it reduces to "non-empty". Assert both explicitly.
- Removing the transit step later is not a standalone deletion: the transit value anchors several
  assertions, so a naive removal is a `NameError`. Name the paired edit in the docstring.
