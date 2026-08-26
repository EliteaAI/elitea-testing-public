---
name: A seed fixture that writes two fields usually declares only one
description: A precondition PUT carrying an extra flag is an undeclared substitution — and if a case reads that flag, it is terminal
type: feedback
aliases: [seed fixture undeclared field, enabled flag substitution, precondition writes the observable, transit seed hides a terminal one]
tags: [area/fidelity, type/review-finding]
created: 2026-08-26
updated: 2026-08-26
---

## The finding

ELITEA-2266/2267/2276 (Project Context), review round 1. A `project_context_seed`
fixture established the precondition with one call:

```python
api.put(path, json={"content": content, "enabled": enabled})   # enabled defaulted to True
```

All three Fidelity Declarations described the substitution as *"seeding a non-empty
Project Context"* — i.e. the **content**. Nobody wrote down that the same `PUT`
also authored `enabled`, and that flag turned out to be:

* ELITEA-2266 step 6 — "An ON/OFF toggle (**enabled by default**)" → an observable
* ELITEA-2267 step 2 — "Verify the toggle is **ON by default**" → an observable
* ELITEA-2276 step 6 — "**Turn** the Project Context toggle **ON**" → a user **ACTION**

So `seed(enabled=True)` + `expect(toggle).to_be_checked()` asserted a value the test
had just written. Terminal substitution, and for 2276 a user action replaced by an
API write — invisible to every gate, because the declaration named the *other* field.

## The habit to build

**Enumerate the fields your precondition write touches, one per row, and check each
against the case text.** "I seeded the entity" is not a declaration; "I seeded
`content`, and `enabled` is carried forward from the product" is. A single-call seed
that sets N fields is N substitutions.

The tell: a substitution passes review when the *reason* for it is true (here: the
toggle genuinely only renders while content is non-empty) — the reason covers one
field and quietly launders the rest.

## The fix shape that generalises

Don't author a field you did not have to author — **carry the product's own value
forward**:

```python
def _seed(content, enabled=None):
    effective = enabled if enabled is not None else _current_enabled()  # GET, then echo
```

`_current_enabled()` mirrors the product's own rule (here literally
`serverData?.enabled ?? true` in the JSX), so the seeded write is byte-identical to
what the product's own Save would send. On a freshly-deleted resource the `GET`
returns the server default, so "X by default" becomes *observed*, not manufactured.

An explicit value then means something precise: **a precondition you are about to act
on**. ELITEA-2276 Phase B seeds `enabled=False` to restore the OFF state its own
earlier real click produced, asserts the switch is unchecked, then **clicks it ON**.
The pre-click assertion is what stops a future regression to the seeded shape.

Related: [[basemodal_close_button_testid_prop]] · [[repairing_a_neighbour_spec_leaves_its_afs_stale]]
