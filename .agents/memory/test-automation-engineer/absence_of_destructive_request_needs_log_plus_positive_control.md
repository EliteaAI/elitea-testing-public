---
name: "'The control deleted nothing' is a request-log claim, and needs a positive control"
description: A surviving row is satisfied by an in-flight DELETE too; and a persistent request observer that was never wired makes `assert not requests` pass vacuously
type: feedback
aliases: [no DELETE fired, table read is not proof, in-flight delete, request log observer, vacuous absence assertion, positive control]
tags: [area/playwright, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## Two traps, one step

A confirmation-dialog flow's defining claim is "the icon opened a dialog and
**deleted nothing**". Both cheap ways of writing it are wrong.

**Trap 1 — reading the table instead of the wire.**

```python
users_page.open_delete_dialog_for_row(row)
expect(users_page.get_row_by_text(email)).to_have_count(1)   # proves nothing
```

A row survives a `DELETE` that is still **in flight**, so this assertion is
satisfied by a destructive control exactly as happily as by a non-destructive
one. The only observable that separates them is the **request log**: a request
is visible the moment the browser *issues* it, long before it resolves.

**Trap 2 — an absence assertion with nothing proving the observer exists.**

```python
delete_requests = collect_requests(page)     # if this silently no-ops…
...
assert not delete_requests                   # …this passes forever
```

Pair every absence assertion with a **positive control**: assert the log
non-empty at the point the flow genuinely issues the request (ELITEA-2298:
confirming the dialog → `len(delete_requests) == 1`; ELITEA-2300, which never
deletes in its body → the `finally` cleanup delete). Without it the claim is
unfalsifiable.

## The shape that works

`automation/utils/request_capture.py` → `collect_requests(page, method="DELETE")`
— passive `page.on("request")`, capture-only, no URL filter (a control that must
issue *no* delete should surface a delete of any resource), returns the live list.

Three caller obligations, all in its docstring: register **before** the action;
read **after** an anchor that proves the product settled (the dialog rendered —
`open_delete_dialog_for_row()` waits for it, so it is the anchor); give the
absence a positive control.

Contrast with [[absence_of_request_assertion_must_wrap_its_trigger]]: that entry
covers the `expect_response` idiom, which only sees traffic after `__enter__` and
must therefore wrap its trigger. A persistent `page.on` observer has the opposite
failure mode — it can never be too late, only never wired.

## Verified

2026-08-29, PR #1976 fix round 1 (ELITEA-2298/2300). Red/green confirmed:
`tests/unit/test_request_capture_backs_absence_claims.py`'s source assertions all
fail against pre-fix `HEAD`. Live run 11/11 green, `reruns.json == {}`, 44.86 s.
The finding cost a full review round — the spec was green, the AFS claimed the
request assertion, and no gate objected.

Related: [[absence_of_request_assertion_must_wrap_its_trigger]] · [[absence_guards_must_watch_the_real_mechanism]]
